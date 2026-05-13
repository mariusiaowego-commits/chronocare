#!/usr/bin/env swift
// vision_ocr.swift — macOS Vision Framework OCR
// Usage: swift scripts/vision_ocr.swift /path/to/image.png
// Outputs recognized text to stdout, errors to stderr.

import Foundation
import Vision

// MARK: - Argument parsing

guard CommandLine.argc == 2 else {
    try FileHandle.standardError.write(contentsOf: "Usage: swift vision_ocr.swift <image_path>\n".data(using: .utf8)!)
    exit(1)
}
let imagePath = CommandLine.arguments[1]

// Verify file exists
guard FileManager.default.fileExists(atPath: imagePath) else {
    try FileHandle.standardError.write(contentsOf: "Error: file not found: \(imagePath)\n".data(using: .utf8)!)
    exit(1)
}

// MARK: - Vision availability check

func isVisionAvailable() -> Bool {
    // VNRecognizeTextRequest is available on macOS 10.15+
    if #available(macOS 10.15, *) {
        return true
    }
    return false
}

guard isVisionAvailable() else {
    try FileHandle.standardError.write(contentsOf: "Error: Vision framework not available on this macOS version\n".data(using: .utf8)!)
    exit(1)
}

// MARK: - OCR execution

guard let imageData = FileManager.default.contents(atPath: imagePath) else {
    try FileHandle.standardError.write(contentsOf: "Error: could not read image data: \(imagePath)\n".data(using: .utf8)!)
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate          // Highest accuracy
request.usesLanguageCorrection = false        // Disable to preserve Chinese character sequences
request.recognitionLanguages = ["zh-Hans", "en-US"]  // Chinese Simplified + English

let handler = VNImageRequestHandler(data: imageData, options: [:])

do {
    try handler.perform([request])
} catch {
    try FileHandle.standardError.write(contentsOf: "Error: Vision request failed: \(error.localizedDescription)\n".data(using: .utf8)!)
    exit(1)
}

guard let observations = request.results else {
    // No text found — output empty string to stdout (not an error)
    exit(0)
}

// Sort observations by vertical position (top-to-bottom, left-to-right)
// This preserves natural reading order for multi-line text
let sortedObservations = observations.sorted { obs1, obs2 in
    // Vision bounding box: origin is bottom-left, convert to top-left for screen coords
    let y1 = 1.0 - obs1.boundingBox.origin.y
    let y2 = 1.0 - obs2.boundingBox.origin.y
    // Group by vertical position (within 2% tolerance), then sort by x
    if abs(y1 - y2) > 0.02 {
        return y1 < y2
    }
    return obs1.boundingBox.origin.x < obs2.boundingBox.origin.x
}

var lines: [String] = []
var currentLineY: Double = -1
var currentLineTexts: [String] = []

for obs in sortedObservations {
    let candidate = obs.topCandidates(1).first?.string ?? ""
    let obsY = 1.0 - obs.boundingBox.origin.y

    if currentLineY < 0 {
        currentLineY = obsY
    }

    if abs(obsY - currentLineY) > 0.02 {
        // New line
        if !currentLineTexts.isEmpty {
            lines.append(currentLineTexts.joined(separator: " "))
        }
        currentLineTexts = [candidate]
        currentLineY = obsY
    } else {
        currentLineTexts.append(candidate)
    }
}

// Flush last line
if !currentLineTexts.isEmpty {
    lines.append(currentLineTexts.joined(separator: " "))
}

let output = lines.joined(separator: "\n")
try FileHandle.standardOutput.write(contentsOf: output.data(using: .utf8)!)
exit(0)
