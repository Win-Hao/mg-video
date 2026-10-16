import Foundation
import Vision
import AppKit

// usage: swift ocr.swift <image>   (always uses the accurate recognizer, zh-Hans + en-US; prints lines top to bottom)
let args = CommandLine.arguments
let url = URL(fileURLWithPath: args[1])
guard let img = NSImage(contentsOf: url), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { print("cannot load"); exit(1) }
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = ["zh-Hans", "en-US"]
req.usesLanguageCorrection = true
req.minimumTextHeight = 0
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try handler.perform([req])
let obs = (req.results ?? []).sorted { a, b in
  let ay = a.boundingBox.midY, by = b.boundingBox.midY
  if abs(ay - by) > 0.004 { return ay > by }
  return a.boundingBox.minX < b.boundingBox.minX
}
for o in obs { if let t = o.topCandidates(1).first { print(t.string) } }
