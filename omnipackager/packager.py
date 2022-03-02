import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import yaml

from pychroot import Chroot

from omnipackager import utils


RPMBUILD_FOLDERS = ['BUILD', 'BUILDROOT', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS']

parser = argparse.ArgumentParser(description='clone and manipulate git repositories')
parser.add_argument('--config-file', metavar='<config_file>',
                    dest='config_file', required=True,
                    help='Configuration file')
parser.add_argument('--input-url', metavar='<input_url>',
                    dest='input_url', required=True,
                    help='Input git repo url of the project you want to build')
parser.add_argument('--git-branch', metavar='<git_branch>',
                    dest='git_branch', required=True,
                    help='Input git branch of the project you want to build')
parser.add_argument('--output-dir', metavar='<output_dir>',
                    dest='output_dir', required=True,
                    help='Dir for the outputs')


def omni_interrupt_handler(signum, frame):
    print('\nKeyboard Interrupted! Cleaning Up and Exit!')
    sys.exit(1)


def parse_package_list(list_file):
    if not list_file:
        raise Exception

    with open(list_file, 'r') as inputs:
        input_dict = json.load(inputs)

    package_list = input_dict["packages"]
    return package_list


def parse_pkg_name(input_url):
    user_str_lst = input_url.split('/')
    return user_str_lst[-1].split('.')[0]


def parse_and_install_build_requires(work_dir, pkg_name, chroot_worker):
    # TODO: Parse all kinds of spec names
    spec_file = work_dir + '/' + pkg_name + '/' + pkg_name + '.spec'
    cmd = ['rpmspec', '-q', '--buildrequires', spec_file]
    print('Parsing BuildRequires of package: ' + pkg_name + ' ...')
    ret = subprocess.run(' '.join(cmd), stdout=subprocess.PIPE, shell=True)
    build_requires = ret.stdout.decode().split('\n')

    print('Installing BuildRequires of package: ' + pkg_name + ' ...')
    for pkg in build_requires:
        if pkg:
            print('Installing : ' + pkg + ' ...')
            # TODO: Should support version parsing of rpm buildrequires
            pkg = pkg.split(' ')[0]
            cmd = ['dnf', 'install', '-y', '--installroot', chroot_worker, pkg]
            subprocess.run(' '.join(cmd), shell=True)


def prepare_workspace(config_options, output_dir):
    work_dir = config_options['working_dir']
    print('Preparing workspace at: ' + work_dir)
    chroot_worker = work_dir + '/chroot_worker'
    chroot_worker_repo = chroot_worker + '/etc/yum.repos.d/'
    utils.clean_up_dir(work_dir)
    utils.clean_up_dir(output_dir)
    os.makedirs(work_dir)
    os.makedirs(chroot_worker)
    os.makedirs(chroot_worker_repo)
    os.makedirs(output_dir)

    prepare_toolchain(config_options, chroot_worker, chroot_worker_repo)

    return work_dir, chroot_worker


def prepare_toolchain(config_options, dest_dir, chroot_worker_repo):
    repo_file = config_options['toolchain_repo']
    shutil.copy(repo_file, chroot_worker_repo)

    print('Installing toolchain packages to chroot worker ...')
    toolchain_pkgs = parse_package_list(config_options['toolchain_packages'])
    cmd = ['dnf', 'install', '-y', '--installroot', dest_dir]
    for pkg in toolchain_pkgs:
        print('Installing: ' + pkg + ' ...')
        cmd.append(pkg)
        subprocess.run(' '.join(cmd), shell=True)
        # filesystem package will override the repo file, copy our repo file again
        if pkg == 'filesystem':
            utils.clean_up_dir(chroot_worker_repo)
            os.makedirs(chroot_worker_repo)
            shutil.copy(repo_file, chroot_worker_repo)

    for folder in RPMBUILD_FOLDERS:
        folder_path = dest_dir + '/root/rpmbuild/' + folder
        os.makedirs(folder_path)


def clone_source(src_url, dest_dir, pkg_name, branch=None):
    print('Fetching: ' + pkg_name + ' ...')
    orig_dir = os.getcwd()
    os.chdir(dest_dir)
    cmd = 'git clone '
    if branch:
        cmd = cmd + '-b ' + branch + ' '
    cmd = cmd + src_url
    subprocess.run(cmd, shell=True)
    os.chdir(orig_dir)


def build_pkg(work_dir, pkg_name, chroot_worker, output_dir):
    spec_path = chroot_worker + '/root/rpmbuild/SPECS/'
    src_path = chroot_worker + '/root/rpmbuild/SOURCES/'
    out_path = chroot_worker + '/root/rpmbuild/RPMS/'

    spec_cmd = ['mv', work_dir + '/' + pkg_name + '/' + pkg_name + '.spec',
                spec_path]
    subprocess.run(' '.join(spec_cmd), shell=True)

    src_cmd = ['mv', work_dir + '/' + pkg_name + '/*', src_path]
    subprocess.run(' '.join(src_cmd), shell=True)

    print('Build package ...')
    with Chroot(chroot_worker):
        build_cmd = ['rpmbuild', '-ba', '/root/rpmbuild/SPECS/' + pkg_name + '.spec']
        subprocess.run(' '.join(build_cmd), shell=True)

    output_cmd = ['mv', out_path + '*', output_dir]
    subprocess.run(' '.join(output_cmd), shell=True)


def main():
    signal.signal(signal.SIGINT, omni_interrupt_handler)
    # parse config options and args
    parsed_args = parser.parse_args()
    with open(parsed_args.config_file, 'r') as config_file:
        config_options = yaml.load(config_file, Loader=yaml.SafeLoader)

    input_url= parsed_args.input_url
    output_dir = parsed_args.output_dir

    work_dir, chroot_worker = prepare_workspace(config_options, output_dir)

    pkg_name = parse_pkg_name(input_url)
    clone_source(input_url, work_dir, pkg_name, parsed_args.git_branch)

    parse_and_install_build_requires(work_dir, pkg_name, chroot_worker)

    build_pkg(work_dir, pkg_name, chroot_worker, output_dir)

    print('Package generated at ' + output_dir + ' ...')









