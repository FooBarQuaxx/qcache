#!/bin/sh

# Install a python version that contains all libraries required
# to build the needed librarires for qcache.
apt-get update
apt-get -y install python-dev python-pip
pip install numpy==1.10.1
pip install pandas==0.17.0
pip install numexpr==2.4.4
pip install tornado==4.2.1
pip install docopt==0.6.2
pip install six

# Remove the packages installed in the previous step. Most of them
# are not required to run QCache.
apt-get remove --purge -y python-pip python-dev

AUTO_ADDED_PACKAGES=`apt-mark showauto`
apt-get remove --purge -y $AUTO_ADDED_PACKAGES

# Install a smaller python package. This will be enough to run QCache
apt-get install -y python-minimal curl
curl https://bootstrap.pypa.io/get-pip.py > get-pip.py
python get-pip.py

# Final cleanup
rm get-pip.py
apt-get remove --purge -y curl
rm -rf /var/lib/apt/lists/*