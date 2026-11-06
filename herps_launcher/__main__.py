import sys

if len(sys.argv) > 1:
    from .javamods.cli import main
else:
    from .app import main

raise SystemExit(main())
