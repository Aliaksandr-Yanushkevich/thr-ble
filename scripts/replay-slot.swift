import Foundation
import CoreBluetooth

// One experimental slot-selection write. No bulk initialization, patch dump,
// save command, firmware update, or fixed GATT handle is used.
let args = CommandLine.arguments
guard args.count == 3, args[1] == "--slot", let slot = Int(args[2]), (1...5).contains(slot) else {
    print("Usage: replay-slot --slot 1..5 (pedal OFF; sends one slot selection)")
    exit(args.contains("--help") ? 0 : 2)
}
let midiService = CBUUID(string: "03B80E5A-EDE8-4B33-A751-6CE34EC4C700")
let midiCharacteristic = CBUUID(string: "7772E5DB-3868-4112-A1A9-F2669D106BF3")

final class Probe: NSObject, CBCentralManagerDelegate, CBPeripheralDelegate {
    let slot: Int
    init(slot: Int) { self.slot = slot; super.init() }
    var manager: CBCentralManager!
    var target: CBPeripheral?
    var characteristic: CBCharacteristic?
    var sent = false
    var finishing = false
    var result: Int32 = 1

    func log(_ text: String) { print("\(ISO8601DateFormatter().string(from: Date())) \(text)"); fflush(stdout) }
    func start() {
        manager = CBCentralManager(delegate: self, queue: .main)
        DispatchQueue.main.asyncAfter(deadline: .now() + 45) { self.stop("Timeout", code: 1) }
    }
    func stop(_ reason: String, code: Int32) {
        guard !finishing else { return }
        finishing = true; result = code
        log(reason); manager.stopScan()
        if let p = target, p.state == .connected { manager.cancelPeripheralConnection(p) }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) { exit(code) }
    }
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            log("Scanning for LE_THRII MIDI service")
            central.scanForPeripherals(withServices: [midiService])
        } else if central.state != .unknown && central.state != .resetting {
            stop("Bluetooth unavailable, state=\(central.state.rawValue)", code: 1)
        }
    }
    func centralManager(_ central: CBCentralManager, didDiscover p: CBPeripheral,
                        advertisementData: [String: Any], rssi RSSI: NSNumber) {
        let name = advertisementData[CBAdvertisementDataLocalNameKey] as? String ?? p.name ?? ""
        guard name == "LE_THRII", target == nil else { return }
        target = p; p.delegate = self; central.stopScan()
        log("Found LE_THRII RSSI=\(RSSI); connecting")
        central.connect(p)
    }
    func centralManager(_ central: CBCentralManager, didConnect p: CBPeripheral) {
        log("Connected; discovering MIDI service by UUID")
        p.discoverServices([midiService])
    }
    func centralManager(_ central: CBCentralManager, didFailToConnect p: CBPeripheral, error: Error?) {
        stop("Connection failed: \(String(describing: error))", code: 1)
    }
    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral p: CBPeripheral, error: Error?) {
        if !finishing { stop("Unexpected disconnect: \(String(describing: error))", code: 1) }
    }
    func peripheral(_ p: CBPeripheral, didDiscoverServices error: Error?) {
        guard error == nil, let s = p.services?.first(where: { $0.uuid == midiService }) else {
            stop("MIDI service discovery failed: \(String(describing: error))", code: 1); return
        }
        p.discoverCharacteristics([midiCharacteristic], for: s)
    }
    func peripheral(_ p: CBPeripheral, didDiscoverCharacteristicsFor s: CBService, error: Error?) {
        guard error == nil, let c = s.characteristics?.first(where: { $0.uuid == midiCharacteristic }),
              c.properties.contains(.notify), c.properties.contains(.writeWithoutResponse) else {
            stop("Required MIDI characteristic/properties missing", code: 1); return
        }
        characteristic = c
        log("MIDI characteristic found; subscribing")
        p.setNotifyValue(true, for: c)
    }
    func peripheral(_ p: CBPeripheral, didUpdateNotificationStateFor c: CBCharacteristic, error: Error?) {
        guard error == nil, c.isNotifying else {
            stop("Notification subscription failed: \(String(describing: error))", code: 1); return
        }
        log("Subscribed; waiting 1 second before single write")
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) { self.sendIfReady(p) }
    }
    func peripheralIsReady(toSendWriteWithoutResponse p: CBPeripheral) { sendIfReady(p) }
    func sendIfReady(_ p: CBPeripheral) {
        guard !sent, !finishing, let c = characteristic, c.isNotifying,
              p.canSendWriteWithoutResponse else { return }
        let hex = "8080f000010c24004d010000000b000e000000040000000000000000000080f7"
        var bytes: [UInt8] = []
        var i = hex.startIndex
        while i < hex.endIndex {
            let next = hex.index(i, offsetBy: 2)
            bytes.append(UInt8(hex[i..<next], radix: 16)!); i = next
        }
        bytes[24] = UInt8(slot - 1)
        guard bytes.count <= p.maximumWriteValueLength(for: .withoutResponse) else {
            stop("Negotiated write capacity too small; no write sent", code: 1); return
        }
        sent = true
        log("TX slot=\(slot) UUID=\(c.uuid) bytes=\(bytes.map { String(format: "%02x", $0) }.joined())")
        p.writeValue(Data(bytes), for: c, type: .withoutResponse)
        DispatchQueue.main.asyncAfter(deadline: .now() + 8) {
            self.stop("Write queued once; verify visible slot. ATT Write Command has no delivery acknowledgment.", code: 0)
        }
    }
    func peripheral(_ p: CBPeripheral, didUpdateValueFor c: CBCharacteristic, error: Error?) {
        if let e = error { log("RX error: \(e)"); return }
        if let data = c.value { log("RX \(data.map { String(format: "%02x", $0) }.joined())") }
    }
}
let probe = Probe(slot: slot)
probe.start()
RunLoop.main.run()
