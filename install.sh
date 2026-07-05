#!/bin/sh
# IPAudio v8.02 Installer Script
# GitHub: https://github.com/memobsa/IPaudio-v8.02

VERSION='8.02'
TEMPATH='/tmp'
PLUGINPATH='/usr/lib/enigma2/python/Plugins/Extensions/IPAudio'
BINDIR='/usr/bin/'
CHECK='/tmp/check'
URL="https://raw.githubusercontent.com/memobsa/IPaudio-v8.02/main/ipaudio_8.02.tar.gz"

echo "========================================="
echo "   Downloading And Installing IPAudio    "
echo "                v$VERSION                "
echo "========================================="

echo "Cleaning up previous installations..."
rm -rf $PLUGINPATH >/dev/null 2>&1
rm -f /usr/bin/gst1.0-ipaudio >/dev/null 2>&1
rm -f /usr/bin/ff-ipaudio >/dev/null 2>&1
rm -f /tmp/ipaudio_*.tar.gz >/dev/null 2>&1
rm -rf /tmp/ipaudio >/dev/null 2>&1
killall -9 gst1.0-ipaudio >/dev/null 2>&1
killall -9 ff-ipaudio >/dev/null 2>&1

cd $TEMPATH
uname -m > $CHECK

echo "Downloading IPAudio v$VERSION from GitHub..."
wget -q "--no-check-certificate" $URL -O ipaudio_${VERSION}.tar.gz

if [ -f "ipaudio_${VERSION}.tar.gz" ]; then
    echo "Extracting files..."
    mkdir -p /tmp/ipaudio
    tar -xzf ipaudio_${VERSION}.tar.gz -C /tmp/ipaudio
else
    echo "❌ Error: Failed to download the archive."
    exit 1
fi

# ==========================================
# DEPENDENCY CHECK & INSTALLATION
# ==========================================
echo "Checking dependencies..."

if [ -f /var/lib/dpkg/status ]; then
    STATUS='/var/lib/dpkg/status'
    OS='DreamOS'
else
    STATUS='/var/lib/opkg/status'
    OS='Opensource'
fi

gstVol='Missing'
gstOss='Missing'
gstMp3='Missing'
equalizer='Missing'

if grep -q 'gstreamer1.0-plugins-base-volume' $STATUS; then gstVol='Installed'; fi
if grep -q 'gstreamer1.0-plugins-good-ossaudio' $STATUS; then gstOss='Installed'; fi
if grep -q 'gstreamer1.0-plugins-good-mpg123' $STATUS; then gstMp3='Installed'; fi
if grep -q 'gstreamer1.0-plugins-good-equalizer' $STATUS; then equalizer='Installed'; fi

if [ "$gstVol" = "Installed" ] && [ "$gstOss" = "Installed" ] && [ "$gstMp3" = "Installed" ] && [ "$equalizer" = "Installed" ]; then
    echo "All dependencies are installed."
else
    echo "=========================================================================="
    echo "Some dependencies need to be downloaded from feeds..."
    echo "=========================================================================="
    
    if [ "$OS" = "DreamOS" ]; then
        echo "apt update ..."
        apt-get update >/dev/null 2>&1
        [ "$gstVol" = "Missing" ] && echo "Downloading gstreamer1.0-plugins-base-volume..." && apt-get install gstreamer1.0-plugins-base-volume -y
        [ "$gstOss" = "Missing" ] && echo "Downloading gstreamer1.0-plugins-good-ossaudio..." && apt-get install gstreamer1.0-plugins-good-ossaudio -y
        [ "$gstMp3" = "Missing" ] && echo "Downloading gstreamer1.0-plugins-good-mpg123..." && apt-get install gstreamer1.0-plugins-good-mpg123 -y
        [ "$equalizer" = "Missing" ] && echo "Downloading gstreamer1.0-plugins-good-equalizer..." && apt-get install gstreamer1.0-plugins-good-equalizer -y
    else
        echo "opkg update ..."
        opkg update >/dev/null 2>&1
        [ "$gstVol" = "Missing" ] && echo "Downloading gstreamer1.0-plugins-base-volume..." && opkg install gstreamer1.0-plugins-base-volume
        [ "$gstOss" = "Missing" ] && echo "Downloading gstreamer1.0-plugins-good-ossaudio..." && opkg install gstreamer1.0-plugins-good-ossaudio
        [ "$gstMp3" = "Missing" ] && echo "Downloading gstreamer1.0-plugins-good-mpg123..." && opkg install gstreamer1.0-plugins-good-mpg123
        [ "$equalizer" = "Missing" ] && echo "Downloading gstreamer1.0-plugins-good-equalizer..." && opkg install gstreamer1.0-plugins-good-equalizer
    fi
fi

# Final check for critical dependency
if ! grep -q 'gstreamer1.0-plugins-base-volume' $STATUS; then
    echo "#########################################################"
    echo "#  gstreamer1.0-plugins-base-volume not found in feed   #"
    echo "#         IPAudio has not been installed                #"
    echo "#########################################################"
    rm -rf /tmp/ipaudio
    rm -f $CHECK
    rm -f ipaudio_${VERSION}.tar.gz
    exit 1
fi

# ==========================================
# BINARIES INSTALLATION
# ==========================================
ARCH=$(cat $CHECK)
echo "[ Your device is $ARCH ]"

if grep -qs -i 'mips' $CHECK; then
    echo "Copying MIPS binaries..."
    cp -a /tmp/ipaudio/bin/mips/* $BINDIR 2>/dev/null
elif grep -qs -i 'armv7l' $CHECK || echo "$ARCH" | grep -qi 'arm'; then
    echo "Copying ARM binaries..."
    if [ -d "/tmp/ipaudio/bin/arm" ]; then
        cp -a /tmp/ipaudio/bin/arm/* $BINDIR 2>/dev/null
    else
        find /tmp/ipaudio -name "gst1.0-ipaudio" -exec cp {} $BINDIR/ \; 2>/dev/null
        find /tmp/ipaudio -name "ff-ipaudio" -exec cp {} $BINDIR/ \; 2>/dev/null
    fi
elif grep -qs -i 'sh4' $CHECK; then
    echo "Copying SH4 binaries..."
    cp -a /tmp/ipaudio/bin/sh4/* $BINDIR 2>/dev/null
elif grep -qs -i 'aarch64' $CHECK; then
    echo "Copying AARCH64 binaries..."
    cp -a /tmp/ipaudio/bin/aarch64/* $BINDIR 2>/dev/null
else
    echo "###############################"
    echo "## Your architecture is not specifically listed. Using fallback ##"
    echo "###############################"
    find /tmp/ipaudio -name "gst1.0-ipaudio" -exec cp {} $BINDIR/ \; 2>/dev/null
    find /tmp/ipaudio -name "ff-ipaudio" -exec cp {} $BINDIR/ \; 2>/dev/null
fi

if [ -f "/usr/bin/gst1.0-ipaudio" ]; then chmod 0775 /usr/bin/gst1.0-ipaudio; fi
if [ -f "/usr/bin/ff-ipaudio" ]; then chmod 0775 /usr/bin/ff-ipaudio; fi

# ==========================================
# PLUGIN FILES INSTALLATION
# ==========================================
echo "Copying files to system..."

mkdir -p $PLUGINPATH
if [ -d "/tmp/ipaudio/usr/lib/enigma2/python/Plugins/Extensions/IPAudio" ]; then
     cp -r /tmp/ipaudio/usr/lib/enigma2/python/Plugins/Extensions/IPAudio/* $PLUGINPATH/ 2>/dev/null
     INSTALL_STATUS="SUCCESS"
elif [ -d "/tmp/ipaudio/usr" ]; then
    cp -r /tmp/ipaudio/usr/* $PLUGINPATH/ 2>/dev/null
    INSTALL_STATUS="SUCCESS"
else
    echo "❌ Error: Invalid archive structure. Core files not found."
    INSTALL_STATUS="FAILED"
fi

mkdir -p /etc/enigma2
if [ -f "/tmp/ipaudio/etc/ipaudio.json" ] && [ ! -f "/etc/enigma2/ipaudio.json" ]; then
    cp /tmp/ipaudio/etc/ipaudio.json /etc/enigma2/
fi

if [ -f "/tmp/ipaudio/etc/asound.conf" ] && [ ! -f "/etc/asound.conf" ]; then
    cp /tmp/ipaudio/etc/asound.conf /etc/
fi

echo "Cleaning up temporary files..."
rm -rf /tmp/ipaudio
rm -f ipaudio_${VERSION}.tar.gz
rm -f $CHECK

echo "========================================="
if [ "$INSTALL_STATUS" = "SUCCESS" ]; then
    echo "       ✅ Installation Completed!        "
    echo "       Restarting Enigma2 GUI...         "
    echo "========================================="
    killall -9 enigma2
else
    echo "       ❌ Installation Failed!           "
    echo "========================================="
fi

exit 0
