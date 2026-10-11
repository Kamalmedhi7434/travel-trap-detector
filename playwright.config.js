import {defineConfig} from '@playwright/test';
import {existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
const windows=process.platform==='win32';
const candidates=windows?['C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe']:process.platform==='darwin'?['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']:['/usr/bin/google-chrome','/usr/bin/chromium'];
const chrome=process.env.CHROME_BIN||candidates.find(existsSync);
const python=windows?'.venv\\Scripts\\python.exe':'.venv/bin/python';
export default defineConfig({testDir:'./tests',testMatch:'*.spec.js',workers:1,timeout:60000,use:{baseURL:'http://127.0.0.1:5000',headless:true,launchOptions:{executablePath:chrome,args:windows?[]:['--no-sandbox']}},webServer:{command:`${python} app.py`,env:{TRAVEL_DB:join(tmpdir(),'travel-ui.db')},url:'http://127.0.0.1:5000',reuseExistingServer:false}});
