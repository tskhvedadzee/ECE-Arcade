#pragma once

// Firmware update mode. Starts an access point and waits for an upload over
// the network, then reboots into the new firmware. Never returns.
void runOtaMode();
