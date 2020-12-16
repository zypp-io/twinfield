import logging

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d [%(levelname)-5s] [%(name)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

MODULES = {
    "100": "openstaande_debiteuren",
    "200": "openstaande_crediteuren",
    "030_1": "mutaties",
    "040_1": "consolidatie",
}

# time out for requests set on 30 min.
TIME_OUT = 2400
