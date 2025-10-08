import pytest
from unittest.mock import patch

# Mock configuration data
MOCK_CONFIG = {
    "categories": {
        "currencies": [
            "usd", "eur", "jpy", "gbp", "aud", "cad", "chf", "nzd", "sgd",
            "hkd", "nok", "sek", "dkk", "mxn", "zar", "try", "cnh", "pln",
            "czk", "huf",
        ],
        "metals": ["xau", "xag", "xpd", "xpt"],
        "commodities": [
            "wtico_usd", "brent_crude_oil", "nat_gas_usd", "corn_usd",
            "wheat_usd", "soybn_usd", "sugar_usd", "cocoa_usd", "coffee_usd",
        ],
        "indices": [
            "us30_usd", "us_30_usd", "spx500_usd", "us_spx_500", "nas100_usd",
            "us_nas_100", "us2000_usd", "us_2000", "uk100_gbp", "uk_100",
            "de40_eur", "de_30_eur", "de_40_eur", "eu50_eur", "eu_50_eur",
            "fr40_eur", "fr_40", "jp225_usd", "jp_225", "au200_aud",
            "au_200", "hk33_hkd", "hk_hsi", "cn50_usd", "cn_50",
            "sg30_sgd", "sg_30",
        ],
        "bonds": [
            "de_10yr_bund", "us_2yr_tnote", "us_5yr_tnote", "us_10yr_tnote",
            "usb02y_usd", "usb05y_usd", "de10yb_eur",
        ],
    }
}

# Patch the config object before importing Model
with patch('src.model.config', MOCK_CONFIG):
    from src.model import Model


@pytest.fixture
def model_instance():
    return Model()


def test_categorize_forex(model_instance):
    assert model_instance.categorize_instrument("EUR/USD") == "Forex"
    assert model_instance.categorize_instrument("GBP_JPY") == "Forex"


def test_categorize_metals(model_instance):
    assert model_instance.categorize_instrument("XAU/USD") == "Metals"
    assert model_instance.categorize_instrument("XAG_USD") == "Metals"


def test_categorize_commodities(model_instance):
    assert model_instance.categorize_instrument("WTICO_USD") == "Commodities"
    assert model_instance.categorize_instrument("NAT_GAS_USD") == "Commodities"


def test_categorize_indices(model_instance):
    assert model_instance.categorize_instrument("US30_USD") == "Indices"
    assert model_instance.categorize_instrument("JP225_USD") == "Indices"


def test_categorize_bonds(model_instance):
    assert model_instance.categorize_instrument("DE10YB_EUR") == "Bonds"
    assert model_instance.categorize_instrument("USB02Y_USD") == "Bonds"


def test_categorize_cfds(model_instance):
    assert model_instance.categorize_instrument("SOME_INSTRUMENT_CFD") == "CFDs"


def test_categorize_other(model_instance):
    assert model_instance.categorize_instrument("UNKNOWN_INSTRUMENT") == "Other"
    assert model_instance.categorize_instrument("EUR/TRY_CFD") == "CFDs" # CFD takes precedence


def test_categorize_case_insensitivity(model_instance):
    assert model_instance.categorize_instrument("eur/usd") == "Forex"
    assert model_instance.categorize_instrument("xau_usd") == "Metals"
    assert model_instance.categorize_instrument("wtico_usd") == "Commodities"


def test_categorize_with_different_separators(model_instance):
    assert model_instance.categorize_instrument("EUR-USD") == "Other" # Not in config
    assert model_instance.categorize_instrument("EUR.USD") == "Other" # Not in config
