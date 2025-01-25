import math


def fix_multipart_params(size: int, parts: int | None =None, part_size: int | None=None) -> tuple[int, int]:
    """Get multipart params consistent with AWS multipart upload constraints.
    
    Given the total 'size' of an S3 object (in bytes), and optionally
    the desired 'parts' (number of parts) and/or 'part_size' (bytes),
    return a tuple (parts, part_size) that satisfy AWS multipart
    upload constraints.

    AWS Constraints:
    - Max object size: 5 TiB
    - Max number of parts: 10,000
    - Part sizes between 5 MiB and 5 GiB (except the last part can be smaller)
    """
    # Constants
    MAX_OBJECT_SIZE = 5 * 1024**4           # 5 TiB
    MAX_PARTS = 10_000
    MIN_PART_SIZE = 5 * 1024 * 1024         # 5 MiB
    MAX_PART_SIZE = 5 * 1024**3            # 5 GiB

    # 1. Validate the total size
    if size < 0:
        raise ValueError("Size cannot be negative.")
    if size == 0:
        # Edge case: a zero-byte object can be uploaded in a single part
        return (1, 0)  # 0-byte part is valid in practice for a zero-byte file

    if size > MAX_OBJECT_SIZE:
        raise ValueError(f"Size exceeds maximum S3 object size of {MAX_OBJECT_SIZE} bytes (5 TiB).")

    # Helper to clamp a part_size within valid range
    def clamp_part_size(ps: int) -> int:
        return max(MIN_PART_SIZE, min(ps, MAX_PART_SIZE))

    # We will compute final_parts and final_part_size in a systematic way.
    # Start with any user-provided values, but adjust them to satisfy constraints.

    # Case A: If both parts and part_size are provided
    if parts is not None and part_size is not None:
        # Ensure parts is within [1, 10_000]
        if parts < 1 or parts > MAX_PARTS:
            raise ValueError(f"'parts' must be in the range [1, {MAX_PARTS}].")

        # Clamp part_size into [5 MiB, 5 GiB]
        part_size = clamp_part_size(part_size)

        # Check how many parts would actually be needed if we use this part_size
        needed_parts = math.ceil(size / part_size)

        if needed_parts > MAX_PARTS:
            raise ValueError(
                f"With part_size={part_size} bytes, you would need {needed_parts} parts, "
                f"which exceeds the max of {MAX_PARTS}."
            )

        if needed_parts != parts:
            parts = needed_parts

        return (parts, part_size)

    # Case B: If only 'parts' is provided
    elif parts is not None:
        if parts < 1 or parts > MAX_PARTS:
            raise ValueError(f"'parts' must be in the range [1, {MAX_PARTS}].")

        # Compute the part_size needed for that many parts
        rough_part_size = math.ceil(size / parts)

        # Clamp it to valid range
        part_size_clamped = clamp_part_size(rough_part_size)

        # Recompute the number of parts with the clamped size
        final_parts = math.ceil(size / part_size_clamped)

        if final_parts > MAX_PARTS:
            raise ValueError(
                f"Requested {parts} parts but cannot satisfy with AWS limits. "
                "Try fewer parts or do not specify 'parts'."
            )

        return (final_parts, part_size_clamped)

    # Case C: If only 'part_size' is provided
    elif part_size is not None:
        # Clamp the requested part_size to [5 MiB, 5 GiB]
        part_size_clamped = clamp_part_size(part_size)

        # Calculate how many parts that implies
        final_parts = math.ceil(size / part_size_clamped)

        if final_parts > MAX_PARTS:
            # We need to increase part_size to reduce the number of parts
            # part_size_needed >= size / MAX_PARTS
            new_part_size = math.ceil(size / MAX_PARTS)

            # Clamp again
            new_part_size = clamp_part_size(new_part_size)
            final_parts = math.ceil(size / new_part_size)

            if final_parts > MAX_PARTS:
                raise ValueError(
                    "Cannot upload within AWS constraints even after adjusting part_size. "
                    f"size={size}, part_size_requested={part_size}, new_part_size={new_part_size}, parts={final_parts}"
                )

            return (final_parts, new_part_size)
        else:
            return (final_parts, part_size_clamped)

    # Case D: Neither 'parts' nor 'part_size' provided
    else:
        # Strategy: pick the maximum possible number of parts up to 10,000
        # i.e., start with the smallest valid part size (5 MiB),
        # and only increase it if we exceed 10,000 parts.

        max_parts_possible = math.ceil(size / MIN_PART_SIZE)

        if max_parts_possible <= MAX_PARTS:
            # We can use the minimum part size of 5 MiB and still not exceed 10,000 parts
            final_parts = max_parts_possible
            chosen_part_size = MIN_PART_SIZE
        else:
            # 5 MiB parts would create too many parts (>10,000).
            # We must increase part_size enough to reduce the count to 10,000 or fewer.
            chosen_part_size = math.ceil(size / MAX_PARTS)
            chosen_part_size = clamp_part_size(chosen_part_size)  # still enforce [5MiB..5GiB]

            final_parts = math.ceil(size / chosen_part_size)
            if final_parts > MAX_PARTS:
                raise ValueError(
                    "Cannot satisfy AWS multipart constraints with 10,000 parts. "
                    f"Size={size}, chosen_part_size={chosen_part_size}, parts={final_parts}"
                )

        return (final_parts, chosen_part_size)

# -------------- TEST EXAMPLES ----------------
if __name__ == "__main__":
    # Example usage
    total_size = 50 * 1024 * 1024  # 50 MB

    # No parts or part_size specified
    p, ps = fix_multipart_params(total_size)
    print("No hints:", p, ps)

    # Only parts specified
    p, ps = fix_multipart_params(total_size, parts=2)
    print("Only parts=2:", p, ps)

    # Only part_size specified
    p, ps = fix_multipart_params(total_size, part_size=5 * 1024 * 1024)  # 5 MB
    print("Only part_size=5MB:", p, ps)

    # Both parts and part_size specified
    p, ps = fix_multipart_params(total_size, parts=3, part_size=6 * 1024 * 1024)
    print("parts=3, part_size=6MB:", p, ps)
