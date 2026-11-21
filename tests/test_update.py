import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import update

# Precios horarios PVPC del 18/11/2026 en €/MWh (de la respuesta real de REData)
V = [79.55,74.99,74.99,75.22,75.13,73.95,100.18,136.99,164.82,155.09,197.06,184.06,
     181.03,171.66,122.34,145.74,176.4,214.57,290.66,293.79,318.17,303.53,196.88,165.08]

def payload(vals):
    return {"data": {}, "included": [
        {"type": "Precio mercado spot", "attributes": {"values": [{"value": 1, "datetime": "2026-11-18T00:00:00.000+01:00"}]}},
        {"type": "PVPC", "attributes": {"values": [
            {"value": v, "datetime": f"2026-11-18T{h:02d}:00:00.000+01:00"} for h, v in enumerate(vals)]}}]}

class T(unittest.TestCase):
    def test_pvpc(self):
        r = update.resumen_dia("2026-11-18", update.parse_pvpc(payload(V)))
        self.assertAlmostEqual(r["avg"], 0.1655, places=4)
        self.assertEqual((r["min_h"], r["max_h"]), (5, 20))
        self.assertAlmostEqual(r["max"], 0.3182, places=4)
    def test_dia_incompleto(self):
        self.assertIsNone(update.resumen_dia("2026-11-18", update.parse_pvpc(payload(V[:10]))))
    def test_sin_pvpc(self):
        self.assertEqual(update.parse_pvpc({"included": []}), [])
    def test_comprobar(self):
        html = "<td>0,1659\xa0€/kWh</td><td>0.1159</td>"
        self.assertEqual(update.comprobar_pagina(html, ["0,1659", "0,1159", "0,0969"]), ["0,0969"])

if __name__ == "__main__":
    unittest.main()
