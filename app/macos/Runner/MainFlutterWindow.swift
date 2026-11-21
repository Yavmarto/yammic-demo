import Cocoa
import FlutterMacOS

class MainFlutterWindow: NSWindow {
  override func awakeFromNib() {
    let flutterViewController = FlutterViewController()
    let windowFrame = self.frame
    self.contentViewController = flutterViewController
    // Demo laptop size; minimum keeps the sidebar and review panes usable.
    self.setFrame(NSRect(x: windowFrame.origin.x, y: windowFrame.origin.y, width: 1440, height: 900), display: true)
    self.minSize = NSSize(width: 1024, height: 700)

    RegisterGeneratedPlugins(registry: flutterViewController)

    super.awakeFromNib()
    self.setContentSize(NSSize(width: 1440, height: 900))
    self.center()
  }
}
