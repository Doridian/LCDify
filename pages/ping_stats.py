from driver import LCDDriver
from page_updating import UpdatingLCDPage
from prometheus import query_prometheus
from utils import LEDColorPreset

class PingStatsLCDPage(UpdatingLCDPage):
    def __init__(self, config, driver: LCDDriver):
        super().__init__(config, driver, "PING RTT / LOSS")
        self.ping_rtt_res = None
        self.packet_loss_res = None

    def _calc_loss_led(self, loss: float):
        if loss < 5:
            return LEDColorPreset.NORMAL
        elif loss < 90:
            return LEDColorPreset.WARNING
        else:
            return LEDColorPreset.CRITICAL

    def _calc_rtt_led(self, rtt: float, warn: float, crit: float):
        if rtt < warn:
            return LEDColorPreset.NORMAL
        elif rtt < crit:
            return LEDColorPreset.WARNING
        else:
            return LEDColorPreset.CRITICAL

    def update(self):
        self.ping_rtt_res = query_prometheus("ping_average_response_ms > 0")
        self.packet_loss_res = query_prometheus("ping_percent_packet_loss")

    def render(self):
        super().render()

        if self.ping_rtt_res is None or self.packet_loss_res is None:
            self.driver.set_line(1, "Loading...")
            return

        lte_rtt = None
        eth_rtt = None
        wan_rtt = None
        for rtt in self.ping_rtt_res["result"]:
            val = float(rtt["value"][1])
            name = rtt["metric"]["name"]

            if name == "lte":
                lte_rtt = val
            elif name == "wired":
                eth_rtt = val
            elif name == "internet":
                wan_rtt = val

        lte_loss = None
        eth_loss = None
        wan_loss = None
        for loss in self.packet_loss_res["result"]:
            val = float(loss["value"][1])
            name = loss["metric"]["name"]

            if name == "lte":
                lte_loss = val
            elif name == "wired":
                eth_loss = val
            elif name == "internet":
                wan_loss = val

        self.driver.set_led(1, LEDColorPreset.get_most_critical([
            self._calc_loss_led(wan_loss),
            self._calc_rtt_led(wan_rtt, 10, 50)
        ]).value)
        self.driver.set_led(2, LEDColorPreset.get_most_critical([
            self._calc_loss_led(eth_loss),
            self._calc_rtt_led(eth_rtt, 10, 50)
        ]).value)
        self.driver.set_led(3, LEDColorPreset.get_most_critical([
            self._calc_loss_led(lte_loss),
            self._calc_rtt_led(lte_rtt, 100, 300)
        ]).value)

        self.driver.set_line(1, f"WAN {wan_rtt:3.0f} ms / {wan_loss:3.0f} %")
        self.driver.set_line(2, f"ETH {eth_rtt:3.0f} ms / {eth_loss:3.0f} %")
        self.driver.set_line(3, f"LTE {lte_rtt:3.0f} ms / {lte_loss:3.0f} %")

PAGE = PingStatsLCDPage
