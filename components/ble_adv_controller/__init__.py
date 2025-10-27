import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.core import ID
from esphome.const import (
    CONF_DURATION,
    CONF_ID,
    CONF_NAME,
    CONF_REVERSED,
    CONF_TYPE,
    CONF_INDEX,
    CONF_VARIANT,
    PLATFORM_ESP32,
)
from esphome.core.entity_helpers import setup_entity
from .const import (
    CONF_BLE_ADV_CONTROLLER_ID,
    CONF_BLE_ADV_ENCODING,
    CONF_BLE_ADV_FORCED_ID,
    CONF_BLE_ADV_MAX_DURATION,
    CONF_BLE_ADV_SEQ_DURATION,
    CONF_BLE_ADV_SHOW_CONFIG,
)

AUTO_LOAD = ["esp32_ble", "select", "number"]
DEPENDENCIES = ["esp32"]
MULTI_CONF = True

# ESPHome C++ namespaces and classes
bleadvcontroller_ns = cg.esphome_ns.namespace('bleadvcontroller')
BleAdvController = bleadvcontroller_ns.class_('BleAdvController', cg.Component, cg.EntityBase)
BleAdvEncoder = bleadvcontroller_ns.class_('BleAdvEncoder')
BleAdvMultiEncoder = bleadvcontroller_ns.class_('BleAdvMultiEncoder', BleAdvEncoder)
BleAdvHandler = bleadvcontroller_ns.class_('BleAdvHandler', cg.Component)
BleAdvEntity = bleadvcontroller_ns.class_('BleAdvEntity', cg.Component)

FanLampEncoderV1 = bleadvcontroller_ns.class_('FanLampEncoderV1')
FanLampEncoderV2 = bleadvcontroller_ns.class_('FanLampEncoderV2')
ZhijiaEncoderV0 = bleadvcontroller_ns.class_('ZhijiaEncoderV0')
ZhijiaEncoderV1 = bleadvcontroller_ns.class_('ZhijiaEncoderV1')
ZhijiaEncoderV2 = bleadvcontroller_ns.class_('ZhijiaEncoderV2')

# Define BLE encoder variants
BLE_ADV_ENCODERS = {
    "fanlamp_pro": {
        "variants": {
            "v1": {"class": FanLampEncoderV1, "args": [0x83, False], "max_forced_id": 0xFFFFFF, "ble_param": [0x19, 0x03], "header": [0x77, 0xF8]},
            "v2": {"class": FanLampEncoderV2, "args": [[0x10, 0x80, 0x00], 0x0400, False], "ble_param": [0x19, 0x03], "header": [0xF0, 0x08]},
            "v3": {"class": FanLampEncoderV2, "args": [[0x20, 0x80, 0x00], 0x0400, True], "ble_param": [0x19, 0x03], "header": [0xF0, 0x08]},
        },
        "default_variant": "v3",
        "default_forced_id": 0,
    },
    "lampsmart_pro": {
        "variants": {
            "v1": {"class": FanLampEncoderV1, "args": [0x81], "max_forced_id": 0xFFFFFF, "ble_param": [0x19, 0x03], "header": [0x77, 0xF8]},
            "v2": {"class": FanLampEncoderV2, "args": [[0x10, 0x80, 0x00], 0x0100, False], "ble_param": [0x19, 0x03], "header": [0xF0, 0x08]},
            "v3": {"class": FanLampEncoderV2, "args": [[0x30, 0x80, 0x00], 0x0100, True], "ble_param": [0x19, 0x03], "header": [0xF0, 0x08]},
        },
        "default_variant": "v3",
        "default_forced_id": 0,
    },
    "zhijia": {
        "variants": {
            "v0": {"class": ZhijiaEncoderV0, "args": [], "max_forced_id": 0xFFFF, "ble_param": [0x1A, 0xFF], "header": [0xF9, 0x08, 0x49]},
            "v1": {"class": ZhijiaEncoderV1, "args": [], "max_forced_id": 0xFFFFFF, "ble_param": [0x1A, 0xFF], "header": [0xF9, 0x08, 0x49]},
            "v2": {"class": ZhijiaEncoderV2, "args": [], "max_forced_id": 0xFFFFFF, "ble_param": [0x1A, 0xFF], "header": [0x22, 0x9D]},
        },
        "default_variant": "v2",
        "default_forced_id": 0xC630B8,
    },
}

# Configuration schema
ENTITY_BASE_CONFIG_SCHEMA = cv.Schema({
    cv.Required(CONF_BLE_ADV_CONTROLLER_ID): cv.use_id(BleAdvController),
})

CONTROLLER_BASE_CONFIG = cv.ENTITY_BASE_SCHEMA.extend({
    cv.GenerateID(): cv.declare_id(BleAdvController),
    cv.Optional(CONF_DURATION, default=200): cv.All(cv.positive_int, cv.Range(min=100, max=500)),
    cv.Optional(CONF_BLE_ADV_MAX_DURATION, default=3000): cv.All(cv.positive_int, cv.Range(min=300, max=10000)),
    cv.Optional(CONF_BLE_ADV_SEQ_DURATION, default=100): cv.All(cv.positive_int, cv.Range(min=0, max=150)),
    cv.Optional(CONF_REVERSED, default=False): cv.boolean,
    cv.Optional(CONF_INDEX, default=0): cv.All(cv.positive_int, cv.Range(min=0, max=255)),
})

# Helper validators
def validate_forced_id(config):
    encoding = config[CONF_BLE_ADV_ENCODING]
    variant = config[CONF_VARIANT]
    forced_id = config.get(CONF_BLE_ADV_FORCED_ID, 0)
    max_forced_id = BLE_ADV_ENCODERS[encoding]["variants"][variant].get("max_forced_id", 0xFFFFFFFF)
    if forced_id > max_forced_id:
        raise cv.Invalid(f"Invalid 'forced_id' for {encoding} - {variant}: {forced_id}. Max: {max_forced_id}")
    return config

def validate_legacy_variant(config):
    encoding = config[CONF_BLE_ADV_ENCODING]
    variant = config[CONF_VARIANT]
    pv = BLE_ADV_ENCODERS[encoding]["variants"][variant]
    if pv.get("legacy", False):
        raise cv.Invalid(f"DEPRECATED '{encoding} - {variant}': {pv['msg']}")
    return config

CONFIG_SCHEMA = cv.All(
    cv.Any(*[
        CONTROLLER_BASE_CONFIG.extend({
            cv.Required(CONF_BLE_ADV_ENCODING): cv.one_of(encoding),
            cv.Optional(CONF_VARIANT, default=params["default_variant"]): cv.one_of(*params["variants"].keys()),
            cv.Optional(CONF_BLE_ADV_FORCED_ID, default=params["default_forced_id"]): cv.hex_uint32_t,
        })
        for encoding, params in BLE_ADV_ENCODERS.items()
    ]),
    validate_forced_id,
    validate_legacy_variant,
    cv.only_on([PLATFORM_ESP32]),
)

# Code generation helpers
async def entity_base_code_gen(var, config, platform):
    await cg.register_parented(var, config[CONF_BLE_ADV_CONTROLLER_ID])
    await cg.register_component(var, config)
    await setup_entity(var, config, platform)

class BleAdvRegistry:
    handler = None

    @classmethod
    def get(cls):
        if not cls.handler:
            hdl_id = ID("ble_adv_static_handler", type=BleAdvHandler)
            cls.handler = cg.new_Pvariable(hdl_id)
            # Updated for ESPHome 2025.x
            cg.add(cls.handler.set_component_source(cg.raw_cpp('"ble_adv_handler"')))
            cg.add(cg.App.register_component(cls.handler))
            for encoding, params in BLE_ADV_ENCODERS.items():
                for variant, param_variant in params["variants"].items():
                    if "class" in param_variant:
                        enc_id = ID(f"enc_{encoding}_{variant}", type=param_variant["class"])
                        enc = cg.new_Pvariable(enc_id, encoding, variant, *param_variant["args"])
                        cg.add(enc.set_ble_param(*param_variant["ble_param"]))
                        cg.add(enc.set_header(param_variant["header"]))
                        cg.add(cls.handler.add_encoder(enc))
        return cls.handler

async def to_code(config):
    hdl = BleAdvRegistry.get()
    var = cg.new_Pvariable(config[CONF_ID])
    cg.add(var.set_setup_priority(300))
    await cg.register_component(var, config)
    await setup_entity(var, config, "ble_adv_controller")
    cg.add(var.set_handler(hdl))
    cg.add(var.set_encoding_and_variant(config[CONF_BLE_ADV_ENCODING], config[CONF_VARIANT]))
    cg.add(var.set_min_tx_duration(config.get(CONF_DURATION, 200), 100, 500, 10))
    cg.add(var.set_max_tx_duration(config.get(CONF_BLE_ADV_MAX_DURATION, 3000)))
    cg.add(var.set_seq_duration(config.get(CONF_BLE_ADV_SEQ_DURATION, 100)))
    cg.add(var.set_reversed(config.get(CONF_REVERSED, False)))
    forced_id = config.get(CONF_BLE_ADV_FORCED_ID, config[CONF_ID].id)
    cg.add(var.set_forced_id(forced_id))
