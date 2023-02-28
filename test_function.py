import browser_api
import proxy
from random import randint
import subprocess

# <Path to Tor Browser>
TBB_PATH="~/tor-browser_en-US/."
# <Path to List of URLs>
# URLS = 


## Localhost
P_HOST = "127.0.0.1"
## Port which TB connect to
PL_PORT = 12345
## Port Listening
RL_PORT = 12346
## Localhost
R_HOST = "127.0.0.1"

if __name__ == "__main__":
    ## You can give each session an ID
    sessionid = 1

    ## Proxy to Record decoded Tor Traffic
    subprocess.Popen("python ./proxy.py " + P_HOST + " " + str(PL_PORT) + " " + str(sessionid),shell=True)
    ## Start Package Handler which handles Copies of Recorded tor Packages
    subprocess.Popen("python ./rec_package.py " + R_HOST + " " + str(RL_PORT),shell=True)

    # Start using Tor-Browser List of urls
    tbdriver = browser_api.initialize_tor_browser(TBB_PATH)
    browser_api.set_proxy(tbdriver,str(PL_PORT))
    ## Get file where URLs are listed
    with open(URLS, 'r') as f:
        for line in f:
            browser_api.visit(tbdriver,line)

    browser_api.close_browser(tbdriver)
