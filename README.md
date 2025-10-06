# Home Automation - Intelligent Heating Controller
This exploratory project leverages the Octopus API to calculate when energy is cheapest on the Agile Octopus price plan.
It uses energy rates, which can vary dramatically during the course of the day, to determine when the best times are to switch your heading on and off. It then uses Tuya API to query the state of thermostats and turn on/off at the most cost effective times.

### References
- [Tuya - IoT Core API Reference](https://developer.tuya.com/en/docs/cloud/device-connection-service?id=Kb0b8geg6o761)
- [Tuya - Develop with Python SDK](https://developer.tuya.com/en/docs/iot/device-control-best-practice-python?id=Kav4zc0nphsn5)
- [Octopus - List Electricity Standard Rates](https://developer.octopus.energy/rest/reference/#tag/products/operation/List%20Electricity%20Tariff%20Standard%20Unit%20Rates)