# omni-packager
Build single packages for a single software with user specified git url and branch name.

## Usage
Dependencies: 
- openEuler distro
- Python runtime: `Python 3.8+`
- rpm packages: `dnf`
- pypi packages: check `requirements.txt`

Install：

1. From source:
```shell
git clone https://github.com/omnibuildplatform/omni-packager.git
cd omni-packager && pip install -r requirements.txt
python3 setup.py install
```

2. Using pip(currently you should download the release manually):
```shell
wget https://github.com/omnibuildplatform/omni-packager/releases/download/v0.1.1/omnipackager-0.1.0.tar.gz
pip3 install --prefix / ./omnipackager-0.1.0.tar.gz
```

Simply run(building src-openeuler/binutils, branch openEuler-22.03-LTS as an example):
```shell
omni-packager --config-file /etc/omni-packager/conf.yaml --input-url https://gitee.com/src-openeuler/binutils.git
--git-branch openEuler-22.03-LTS --output-dir /opt/omni-pkg-out/
```

## TODO list

- Support pre-pack toolchain to a tar file
- Support build package from local folder
- Support hierarchical repo search(local -> remote)
- Support BuildRequires version parse
- Support read all kind of spec names
- Support collect SRPM output

## Contribute

Welcome to file issues or bugs at:
https://github.com/omnibuildplatform/omni-packager/issues
