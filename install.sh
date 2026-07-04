#!/bin/sh
# IPAudio v8.02 Installer Script
# GitHub: https://github.com/memobsa/IPaudio-v8.02

VERSION='8.02'
TEMPATH='/tmp'
PLUGINPATH='/usr/lib/enigma2/python/Plugins/Extensions/IPAudio'
URL="https://raw.githubusercontent.com/memobsa/IPaudio-v8.02/main/ipaudio_8.02.tar.gz"

echo "========================================="
echo "   Downloading And Installing IPAudio    "
echo "                v$VERSION                "
echo "========================================="

echo "Cleaning up previous installations..."
rm -rf $PLUGINPATH >/dev/null 2>&1
rm -f /tmp/ipaudio_*.tar.gz >/dev/null 2>&1
rm -rf /tmp/ipaudio >/dev/null 2>&1

cd $TEMPATH

echo "Downloading IPAudio v$VERSION from GitHub..."
wget -q "--no-check-certificate" $URL -O ipaudio_${VERSION}.tar.gz

if [ -f "ipaudio_${VERSION}.tar.gz" ]; then
    echo "Extracting files..."
    mkdir -p /tmp/ipaudio
    tar -xzf ipaudio_${VERSION}.tar.gz -C /tmp/ipaudio
else
    echo "❌ Error: Failed to download the archive."
    echo "Please check the GitHub link or your internet connection."
    exit 1
fi

echo "Copying files to system..."
# دمج مجلد usr المستخرج مع مجلد usr في الرسيفر لوضع الملفات في مسارها بدقة
if [ -d "/tmp/ipaudio/usr" ]; then
    cp -r /tmp/ipaudio/usr/* /usr/ 2>/dev/null
    INSTALL_STATUS="SUCCESS"
else
    echo "❌ Error: Invalid archive structure. Folder 'usr' not found."
    INSTALL_STATUS="FAILED"
fi

echo "Cleaning up temporary files..."
rm -rf /tmp/ipaudio
rm -f ipaudio_${VERSION}.tar.gz

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