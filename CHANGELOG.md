# Changelog
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (`<major>`.`<minor>`.`<patch>`)

## [v1.2.0]
### Changed
* Windowing helper utilities now merge user-specified axes/plot kwargs with defaults, preferring user inputs
* (Internal) Snap checking now utilizes axes native data rather than having to special case multiple numpy datatypes to prevent errors
* Add `NaN` awareness to prevent unexpected behavior when working with datasets containing gaps
* Expand & normalize handling of types expected for xy data, `position`, and `window_width`; all types that matplotlib can plot should also be meaningfully supported

### Fixed
* Fix `DragRect` completely ignoring user-specified redraw callbacks
* Fix `FlexibleRect` not calling the redraw callback when respanning
* Fix incorrect resizing of `DragRect` on axis limit change
* Fix `DragLine` accidentally validating `snap_to` against xdata for vertical lines

## [v1.1.0]
### Changed
* #9 Dragging is now inhibited while another widget has the canvas locked (e.g. zooming/panning)

## [v1.0.1]
### Fixed
* #8 Fix snapping error when plotting timedelta-based axis data

## [v1.0.0]
Initial release - yay!
