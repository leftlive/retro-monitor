# Security Policy

## Supported Versions

Retro Monitor is currently pre-1.0. Security fixes target the latest `main` branch unless a release note says otherwise.

## Reporting a Vulnerability

Please report suspected vulnerabilities by opening a private security advisory on GitHub if available, or by contacting the maintainer privately.

Do not include secrets, Wi-Fi credentials, public IP addresses, SSH keys, Home Assistant tokens, or private telemetry payloads in public issues.

## Local-Network Assumption

Retro Monitor is designed for trusted local networks. The agents expose local HTTP endpoints and are not intended to be exposed directly to the public internet.

If you need remote access, place Home Assistant or another authenticated reverse proxy in front of the service and review the network exposure carefully.
