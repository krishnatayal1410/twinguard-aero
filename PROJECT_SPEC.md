# TwinGuard Aero — Project Specification

## Problem
Fixed-threshold engine monitoring can miss gradual, multi-parameter degradation. TwinGuard maintains a synchronized software representation of the engine and combines engineering context with machine learning to estimate health, developing faults, degradation and mission risk.

## MVP inputs
RPM, throttle, altitude, ambient temperature, CHT, EGT, oil pressure, oil temperature, fuel flow, vibration, battery voltage, operating hours.

## MVP outputs
Current twin state, expected values, residuals, anomaly status, fault probabilities, subsystem health, overall health, proof-of-concept RUL, mission risk and maintenance advice.

## Initial faults
Normal, lubrication degradation, overheating, abnormal vibration, sensor drift.

## MVP success
Healthy simulation -> live dashboard -> fault injection -> residual change -> anomaly -> probable fault -> health/RUL degradation -> future mission simulation -> maintenance recommendation.
