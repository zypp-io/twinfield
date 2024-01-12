<p align="center"><img alt="logo" src="https://www.zypp.io/static/assets/img/logos/zypp/white/500px.png" width="200"></p>

[![Downloads](https://pepy.tech/badge/twinfield)](https://pepy.tech/project/twinfield)
[![Open Source](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://opensource.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI](https://img.shields.io/pypi/v/twinfield)](https://pypi.org/project/twinfield/)
[![Latest release](https://badgen.net/github/release/zypp-io/twinfield)](https://github.com/zypp-io/twinfield/releases)

Twinfield
====

---
> Python package for reading Twinfield data using the Twinfield API.

## Installation

---
```commandline
pip install twinfield
```

## Usage
for an extensive list of examples, please checkout the [twinfield test suite](twinfield/tests/test_twinfield.py).

```python
from twinfield import TwinfieldApi

# logging in
tw = TwinfieldApi()

# sending browse request.
df = tw.query_by_year(code="030_3", year=2021)

# sending dimensions request
df = tw.dimensions(dim_type="CRD")
```
## required environment variables
Twinfield works with OpenID Connect. OpenID Connect is a simple identity layer on top of the OAuth 2.0 protocol.
In order to authenticate with the twinfield server, the following environment variables must be set. Please see the
[Twinfield webservice documentation](https://accounting.twinfield.com/webservices/documentation/#/ApiReference/Authentication/OpenIdConnect)
on the walktrough how to obtain the refresh token and set the app registration.

```shell
"TWINFIELD_ORGANISATION"
"TWINFIELD_CLIENT_ID"
"TWINFIELD_CLIENT_SECRET"
"TWINFIELD_REFRESH_TOKEN"
```

## optional environment variables
TQDM accepts environmental variables to overwrite default settings `TQDM_*` i.e.,
```shell
TQDM_DISABLE=1
TQDM_MININTERVAL=5
```

How to set environment variables?
- [Windows](https://stackoverflow.com/questions/5898131/set-a-persistent-environment-variable-from-cmd-exe)
- [macOS](https://apple.stackexchange.com/questions/106778/how-do-i-set-environment-variables-on-os-x)
- [Linux](https://unix.stackexchange.com/questions/117467/how-to-permanently-set-environmental-variables)

---

## api scoping (security) advice
Please note that there are different levels of API access in Twinfield app's. It is recommended to use level 3 access over level 1 access.
Level 3 is sufficient for working with the dataservices.

### Twinfield deprecation notices
- The module salesinvoice is only to be used if invoices need to be generated. If only the transaction registration is necessary, use the transactions endpoint.
- modules have versions, for instance the 030 module can be pulled with suffix _1 or _3. It is advised to use the latest version because the speed of the requests is greater.


---

[Link](https://www.twinfield.nl/api) to the Twinfield API documentation.

---

For business inquiries concerning this package, contact us at hello@zypp.io
