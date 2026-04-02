from sagemcom_f3896_client.models import (
    ModemModeResult,
    RegistrationResult,
    SoftwareUpdateResult,
)


def test_registration_result_build():
    raw = {
        "registration": {
            "registrationComplete": True,
            "downstreamLocked": True,
        }
    }
    result = RegistrationResult.build(raw)
    assert result.registration_complete is True
    assert result.downstream_locked is True


def test_registration_result_build_false():
    raw = {
        "registration": {
            "registrationComplete": False,
            "downstreamLocked": False,
        }
    }
    result = RegistrationResult.build(raw)
    assert result.registration_complete is False
    assert result.downstream_locked is False


def test_software_update_result_build():
    raw = {"softwareUpdate": {"status": "complete_from_management"}}
    result = SoftwareUpdateResult.build(raw)
    assert result.status == "complete_from_management"


def test_modem_mode_result_build():
    raw = {"modemmode": {"enable": True}}
    result = ModemModeResult.build(raw)
    assert result.enabled is True


def test_modem_mode_result_build_disabled():
    raw = {"modemmode": {"enable": False}}
    result = ModemModeResult.build(raw)
    assert result.enabled is False
