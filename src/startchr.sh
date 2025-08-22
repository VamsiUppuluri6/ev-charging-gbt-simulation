killall python3 -9
killall nodejs
python3 EVCharger.py &
nodejs  BMSDesign.js &
sleep 5
chromium-browser 127.0.0.1:8082/bmsemu.html  --start-fullscreen --kiosk --incognito --noerrdialogs --disable-translate --no-first-run --fast --fast-start --disable-infobars --disable-features=TranslateUI --disable-gpu --disk-cache-dir=/dev/null  
