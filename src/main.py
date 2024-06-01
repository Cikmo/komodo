"""
Main module of the application.
"""

import asyncio
import os

if "nt" not in os.name:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def main():
    """The entry point of the application."""
    print("Hello, World!")
