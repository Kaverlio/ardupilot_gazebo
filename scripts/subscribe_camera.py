#!/usr/bin/env python3
"""Subscribe to a Gazebo camera topic and access raw frames."""

import argparse
import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover - numpy is required.
    raise SystemExit("numpy is required for this script") from exc

try:
    import pygazebo
    from pygazebo.msg import image_pb2, image_stamped_pb2
except ImportError as exc:  # pragma: no cover - provide a helpful hint.
    raise SystemExit(
        "pygazebo is required. Install it with 'sudo apt install python3-pygazebo' "
        "or ensure your Gazebo build exports the Python bindings."
    ) from exc

try:  # OpenCV is optional, used only when --show is passed.
    import cv2  # type: ignore
except ImportError:  # pragma: no cover - optional dependency.
    cv2 = None


@dataclass(frozen=True)
class _FormatInfo:
    dtype: str
    channels: int
    order: str  # Stored order within the Gazebo message (e.g. 'RGB', 'BGR', 'GRAY').


_PIXEL_FORMAT_MAP: Dict[int, _FormatInfo] = {
    image_pb2.Image.L_INT8: _FormatInfo("uint8", 1, "GRAY"),
    image_pb2.Image.RGB_INT8: _FormatInfo("uint8", 3, "RGB"),
    image_pb2.Image.RGBA_INT8: _FormatInfo("uint8", 4, "RGBA"),
    image_pb2.Image.BGR_INT8: _FormatInfo("uint8", 3, "BGR"),
    image_pb2.Image.BGRA_INT8: _FormatInfo("uint8", 4, "BGRA"),
}

# Remapping from the message's layout to the RGB layout returned by decode_frame().
_COLOR_REMAP: Dict[str, Sequence[int]] = {
    "RGB": (),
    "RGBA": (),
    "BGR": (2, 1, 0),
    "BGRA": (2, 1, 0, 3),
    "GRAY": (),
}


def _parse_master(master: str) -> Tuple[str, int]:
    host, _, port = master.partition(":")
    port_value = port or "11345"
    return host or "127.0.0.1", int(port_value)


def decode_frame(image: image_pb2.Image) -> np.ndarray:
    """Convert a Gazebo image message into an RGB (or grayscale) NumPy array."""
    fmt = _PIXEL_FORMAT_MAP.get(image.pixel_format)
    if fmt is None:
        raise ValueError(f"Unsupported pixel format: {image.pixel_format}")

    dtype = np.dtype(fmt.dtype)
    row_stride = image.step // dtype.itemsize
    frame = np.frombuffer(image.data, dtype=dtype)

    if fmt.channels == 1:
        frame = frame.reshape(image.height, row_stride)
        frame = frame[:, : image.width]
        return frame

    frame = frame.reshape(image.height, row_stride)
    frame = frame[:, : image.width * fmt.channels]
    frame = frame.reshape(image.height, image.width, fmt.channels)

    remap = _COLOR_REMAP.get(fmt.order)
    if remap:
        frame = frame[..., remap]

    return frame


def _prepare_display_frame(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        return frame
    if frame.shape[-1] == 3:
        return frame[:, :, ::-1]
    if frame.shape[-1] == 4:
        return frame[:, :, [2, 1, 0, 3]]
    return frame


async def _run(args: argparse.Namespace) -> None:
    address = _parse_master(args.master)
    logging.info("Connecting to Gazebo master at %s:%s", *address)
    manager = await pygazebo.connect(address)

    subscriber = manager.subscribe(
        topic=args.topic,
        msg_type=image_stamped_pb2.ImageStamped,
    )

    frame_counter = 0

    try:
        while True:
            raw_message = await subscriber.recv()

            msg = image_stamped_pb2.ImageStamped()
            if isinstance(raw_message, image_stamped_pb2.ImageStamped):
                msg.CopyFrom(raw_message)
            else:
                msg.ParseFromString(raw_message)

            try:
                frame = decode_frame(msg.image)
            except ValueError as exc:
                logging.warning("Skipping frame: %s", exc)
                continue

            frame_counter += 1
            stamp = msg.time
            timestamp = stamp.sec + stamp.nsec * 1e-9
            print(f"Frame {frame_counter:05d} @ {timestamp:.6f}s -> shape={frame.shape}")

            if args.show:
                if cv2 is None:
                    logging.warning("OpenCV not available; cannot display frames")
                else:
                    display_frame = _prepare_display_frame(frame)
                    cv2.imshow("Gazebo Camera", display_frame)
                    if cv2.waitKey(1) & 0xFF == 27:
                        logging.info("Received ESC, stopping subscription")
                        break

            if args.max_frames and frame_counter >= args.max_frames:
                logging.info("Reached frame limit (%d), stopping", args.max_frames)
                break
    finally:
        unsubscribe = getattr(subscriber, "unsubscribe", None)
        if unsubscribe is not None:
            result = unsubscribe()
            if asyncio.iscoroutine(result):
                await result
        if cv2:
            cv2.destroyAllWindows()


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--master",
        default="127.0.0.1:11345",
        help="Gazebo master to connect to (default: %(default)s)",
    )
    parser.add_argument(
        "--topic",
        default="/gazebo/default/iris_demo/iris_demo/gimbal_small_2d/tilt_link/camera/image",
        help="Camera topic to subscribe to",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Stop after receiving this many frames (0 means run forever)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display frames using OpenCV if available",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level))

    try:
        asyncio.run(_run(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
