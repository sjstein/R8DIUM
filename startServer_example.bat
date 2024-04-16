:: Edit this file for your specific path and ServerConfig filename and
:: rename this file to "startServer.bat" (remove the ""_example") and
:: make sure this file is in the same directory as your Run8 executable
@ECHO OFF
C:
cd "C:\Run8Studios\Run8 Train Simulator V3"
start "" "Run-8 Train Simulator V3.exe" -ServerConfigFile ServerConfig.xml
