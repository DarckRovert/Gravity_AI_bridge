"""
Tests para ThermalWatchdog e IoTController (V30.0 Mythos Edition).
"""

import unittest
from core.thermal_watchdog import ThermalWatchdog
from core.tools.iot_controller import IoTController


class TestThermalAndIoT(unittest.TestCase):

    def test_thermal_watchdog_instantiation(self):
        watchdog = ThermalWatchdog(check_interval=60, max_temp=85.0)
        self.assertFalse(watchdog.running)
        self.assertFalse(watchdog.throttling_active)
        
        # Probar lectura de temperatura
        temp = watchdog.get_cpu_temp()
        self.assertIsInstance(temp, float)
        self.assertGreater(temp, 0.0)

    def test_iot_controller_simulation(self):
        controller = IoTController()
        # Verificar respuesta en simulación (sin HASS activo)
        res = controller.set_lights("studio", "on")
        self.assertIn("studio", res)

        sec_status = controller.get_security_status()
        self.assertIsInstance(sec_status, str)


if __name__ == "__main__":
    unittest.main()
