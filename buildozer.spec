[app]
title = 业忠贸易计算器
package.name = yezhongcalc
package.domain = com.yezhong
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
version = 0.1
requirements = python3,kivy==2.1.0,android,jnius
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.1.0
fullscreen = 0
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET
android.api = 31
android.minapi = 21
android.ndk = 23b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
p4a.branch = release-2022.12.20

[buildozer]
log_level = 2
warn_on_root = 1