from src.model import Model


def test_categorize_instrument():
    model_instance = Model()
    # Forex
    assert model_instance.categorize_instrument("EUR/USD") == "Forex"
    assert model_instance.categorize_instrument("GBP/JPY") == "Forex"
    assert model_instance.categorize_instrument("AUD/CAD") == "Forex"

    # Metals
    assert model_instance.categorize_instrument("XAU/USD") == "Metals"
    assert model_instance.categorize_instrument("XAG/EUR") == "Metals"

    # Commodities
    assert model_instance.categorize_instrument("WTICO/USD") == "Commodities"
    assert model_instance.categorize_instrument("BRENT_CRUDE_OIL") == "Commodities"

    # Indices
    assert model_instance.categorize_instrument("US30/USD") == "Indices"
    assert model_instance.categorize_instrument("DE40/EUR") == "Indices"

    # Bonds
    assert model_instance.categorize_instrument("DE10YB/EUR") == "Bonds"

    # CFDs
    assert model_instance.categorize_instrument("A3M_CFD.ES") == "CFDs"
    assert model_instance.categorize_instrument("AAPL_CFD.US") == "CFDs"

    # Other
    assert model_instance.categorize_instrument("UNKNOWN_INSTRUMENT") == "Other"
