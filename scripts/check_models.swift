// Validate that each published archive can be compiled and loaded by Core ML.
// Usage: swift scripts/check_models.swift dist/models-v1
import CoreML
import Foundation

let root = URL(fileURLWithPath: CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "dist/models-v1")
let work = FileManager.default.temporaryDirectory.appendingPathComponent("unweave-model-check-\(UUID().uuidString)")
try FileManager.default.createDirectory(at: work, withIntermediateDirectories: true)
defer { try? FileManager.default.removeItem(at: work) }

for (name, stems) in [("htdemucs", 4), ("htdemucs_6s", 6)] {
  let archive = root.appendingPathComponent("\(name)-fp32.zip")
  let extracted = work.appendingPathComponent(name)
  let unzip = Process()
  unzip.executableURL = URL(fileURLWithPath: "/usr/bin/ditto")
  unzip.arguments = ["-x", "-k", archive.path, extracted.path]
  try unzip.run()
  unzip.waitUntilExit()
  guard unzip.terminationStatus == 0 else { fatalError("Couldn't extract \(name)") }
  let compiled = try MLModel.compileModel(at: extracted.appendingPathComponent("\(name).mlpackage"))
  defer { try? FileManager.default.removeItem(at: compiled) }
  let configuration = MLModelConfiguration()
  configuration.computeUnits = .cpuAndGPU
  let model = try MLModel(contentsOf: compiled, configuration: configuration)
  let description = model.modelDescription
  for (key, expected) in [("mix", [1, 2, 343980]), ("spec", [1, 4, 2048, 336])] {
    let constraint = description.inputDescriptionsByName[key]!.multiArrayConstraint!
    precondition(constraint.shape.map(\.intValue) == expected, "Unexpected \(key) shape")
    precondition(constraint.dataType == .float32, "Unexpected \(key) precision")
  }
  for (key, expected) in [("freq", [1, stems, 4, 2048, 336]), ("time", [1, stems, 2, 343980])] {
    let constraint = description.outputDescriptionsByName[key]!.multiArrayConstraint!
    precondition(constraint.shape.map(\.intValue) == expected, "Unexpected \(key) shape")
    precondition(constraint.dataType == .float32, "Unexpected \(key) precision")
  }
  print("\(name): archive extracted, compiled, and loaded; FP32 engine interface verified.")
}
