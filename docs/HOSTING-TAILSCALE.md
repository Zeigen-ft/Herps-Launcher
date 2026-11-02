# Private multiplayer over Tailscale (Windows Java 0.2.2)

The host and friends can play from different locations. Tailscale supplies the private network; the Minecraft server must also use the correct address and authentication settings. A message saying **"This server is in online mode"** means the server requires Microsoft authentication. This launcher does not provide Microsoft sign-in.

## Host

1. Install Tailscale on both PCs, connect it, and give your friend access to the host PC through your Tailscale network or device sharing. Both players need Java Edition 26.3-compatible clients and prepared resources in Herspers.
2. Stop the old Minecraft server: type **`stop`** in its console and wait for it to exit. A running server keeps its old authentication settings until restarted.
3. In the extracted **Herspers-Minecraft** application folder, open **Host-Tailscale.cmd**. If asked, read the Minecraft EULA and type **I AGREE** only if you agree.
4. The starter discovers the host's Tailscale IPv4 address, backs up an existing server configuration, sets `online-mode=false`, and binds **only** to that address. It prints an address such as **100.80.12.34:25565**. Give the actual printed address to your friend.
5. Keep the host window open. Type **`stop`** there to save and shut down. An occupied port is reported; the starter never kills other server processes.

The existing `Documents\Herspers-Server` folder is reused if it contains `server.properties`, matching the earlier manual setup. Otherwise the default is `%LOCALAPPDATA%\Herspers Minecraft\servers\tailscale`. The printed server folder contains its world, properties and logs. Configuration backups have unique names; existing worlds, player files and accepted EULAs are preserved.

## Join (host and friend)

Open **Join-Tailscale.cmd**, paste the host's printed address, and enter a distinct player name of 3–16 letters, numbers or underscores. Use the same name on later visits. Private-mode player identities are derived from those names; they differ from authenticated account identities.

**The host also joins the printed Tailscale address.** This server is bound to the Tailscale interface, so `localhost` is not its listening address. You can also use **Multiplayer → Direct Connection** in an existing compatible client.

This is a private server without Microsoft account verification. Invite only the intended friends through Tailscale. It requires no router port forwarding. Tailscale sharing/permissions and Windows Firewall still control whether a friend can reach the server.

## Troubleshooting

- **Still says online mode:** verify the host stopped the old server, launched Host-Tailscale.cmd, and your friend joined its newly printed address. Check `server.properties` in the printed folder; it must contain the current Tailscale `server-ip` and `online-mode=false`.
- **Cannot listen / port occupied:** connect Tailscale, stop the old server, then retry. If you intentionally run another server, choose a different port with the advanced command below.
- **Connection times out:** check Tailscale's device-sharing/network access first. If a Windows Firewall rule is needed, allow this application's `bin\horizon-client.exe` for TCP on the selected port, scoped to the host's Tailscale local address and remote range `100.64.0.0/10`. Do not disable the firewall.
- **Missing resources:** run Setup.cmd once. Existing prepared resources are reused; a new server does not require another resource export.
- **Server error:** retain its console output and `logs\latest.log` in the printed server folder. Client errors are in `%LOCALAPPDATA%\Herspers Minecraft\logs\launcher.log`.

Advanced hosting, from the application folder:

```powershell
.\Herspers-Minecraft.exe --host-tailscale --server-dir "D:\My Private Server" --port 25566
.\Herspers-Minecraft.exe --join-tailscale 100.80.12.34:25566 --name YourName
```

The optional `--accept-eula` flag is for automation only when the operator agrees to the [Minecraft EULA](https://aka.ms/MinecraftEULA). The normal starter asks before accepting a previously unaccepted EULA.

The rebuild checks the real server's configuration parser without assets and tests private-address validation, backups and launch arguments. An actual two-PC Tailscale session still needs validation on the players' machines.
