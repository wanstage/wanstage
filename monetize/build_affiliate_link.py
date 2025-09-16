import os
import re
import sys
import urllib.parse

import yaml
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/WANSTAGE/.env"))


def expand_env(s):
    return re.sub(r"\$\{([^}]+)\}", lambda m: os.getenv(m.group(1), ""), s)


def add_params(url, params):
    u = urllib.parse.urlsplit(url)
    q = dict(urllib.parse.parse_qsl(u.query, keep_blank_values=True))
    q.update({k: v for k, v in params.items() if v})
    new_q = urllib.parse.urlencode(q, doseq=True)
    return urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, new_q, u.fragment))


def main():
    if len(sys.argv) < 2:
        print("")
        return
    url = sys.argv[1]
    rules = yaml.safe_load(open(os.path.expanduser("~/WANSTAGE/monetize/link_rules.yaml")))
    host = urllib.parse.urlsplit(url).netloc
    for r in rules.get("rules", []):
        if r["match"] in host:
            # add affil params
            params = {k: expand_env(v) for k, v in (r.get("add_params") or {}).items()}
            url = add_params(url, params)
            # add utm
            if r.get("utm"):
                utm = rules.get("defaults", {})
                utm_params = {k: expand_env(v) for k, v in utm.items()}
                url = add_params(url, utm_params)
            break
    print(url)


if __name__ == "__main__":
    main()
