Autom
=====
A data recording and video capturing module written in Python for a Chevy Volt.

Requirements
============
* [Python 2.7](https://www.python.org/download/releases/2.7/)
* [OpenCV (Python and C++)](https://github.com/opencv/opencv)
* [pysftp](https://pypi.python.org/pypi/pysftp)
* [pyvit](https://github.com/linklayer/pyvit)
* [ConfigParser](https://docs.python.org/2/library/configparser.html)
* [moviepy](https://pypi.python.org/pypi/moviepy)

Hardware
--------
* [CANtact](https://store.linklayer.com/products/cantact-v1-0?variant=1151776209) OR [CANable](https://www.tindie.com/products/protofusion/canable-usb-to-can-bus-adapter/)
* [Raspberry Pi](https://www.raspberrypi.org/products/) or other small computer/mini PC running Linux (if you use a Pi, you may want to also get a [UPS for it as well](https://www.adafruit.com/product/1944) for data backup operations after the car is turned off)
* Any secondary PC at home that is always on (preferably running some Linux distribution, but not necessary)
* A reasonably priced good to high quality webcamera. Personal recommendation: [Microsoft LifeCam HD-3000](https://www.amazon.com/Microsoft-3364820-LifeCam-HD-3000/dp/B008ZVRAQS)

How To Use Recording
====================
1. Setup an SSH server on a home computer that will always be on.
```bash
sudo apt-get install openssh-server
```
### (Optional) For those who would like to use public/private key authentication to use SFTP
  * Create a public/private key pair on the car PC to use to login to your SSH server instead of using a password
```bash
ssh-keygen -b 4096
```
  * Transfer the public key to the remote home computer
```bash
ssh-copy-id username@hostIP
```
2. Create backup folder in home directory on the remote computer.
```bash
mkdir ~/backup/
```
3. Specify the server IP, username, password, port number (default is 22 for SSH), and make sure `ifPassword = True` and set `sshPass` in [config.cfg](record/config.cfg).
### (Optional) For those using a private key
  * Specify the server IP, username, private key location, port number, and make sure `ifPassword = False` in [config.cfg](record/config.cfg).
4. On PC for car installation, clone a copy of Autom anywhere.
5. Add `gnome-terminal -e "path/to/Autom/run.sh"` to startup applications on the car PC. If you are using Ubuntu, you can do this by `cd`'ing to the root directory of this project and executing the following command: 
```bash
echo -e "[Desktop Entry]\nType=Application\nName=Autom\nExec=gnome-terminal -e \"`pwd`/record/run.sh\"\nIcon=\nComment=\nX-GNOME-Autostart-enabled=true" >> ~/.config/autostart/Autom.desktop
```
6. Make sure car PC has the home network as a known network.
7. Plug in CANtact/CANable into vehicle OBD-II port and then into car PC usb port.
8. Attach webcamera to front of rearview mirror to get a view of the road, then plug into car PC.
9. Attach car PC to vehicle power source.
10. Power on the PC and the car and start driving.