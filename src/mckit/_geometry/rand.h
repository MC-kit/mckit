//
// Header-only pseudo-random number generators.
//
// Replaces the former MKL VSL RNG usage (VSL_BRNG_MT19937 + vdRngUniform)
// with the public-domain xoshiro256** generator by Blackman and Vigna,
// seeded with splitmix64.
//

#ifndef MCKIT_RAND_H
#define MCKIT_RAND_H

#include <cstdint>
#include <random>

/// 64-bit rotate left.
inline uint64_t rotl64(uint64_t x, int k)
{
    return (x << k) | (x >> (64 - k));
}

/// Splitmix64 generator - the standard way to seed xoshiro family generators.
///
/// @param state Pointer to the seed state, advanced on every call.
/// @return Next 64-bit random value.
inline uint64_t splitmix64(uint64_t *state)
{
    uint64_t z = (*state += 0x9E3779B97F4A7C15ull);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
    return z ^ (z >> 31);
}

/// xoshiro256** pseudo-random number generator.
///
/// Fast, high-quality generator suitable for floating point simulations.
/// The all-zero state must be avoided - use seed() for initialization.
struct Xoshiro256ss
{
    uint64_t s[4]; /// Generator state, must not be all zeros.

    /// Initializes the state from an arbitrary 64-bit seed using splitmix64.
    void seed(uint64_t seed_value)
    {
        uint64_t sm_state = seed_value;
        for (int i = 0; i < 4; ++i)
            s[i] = splitmix64(&sm_state);
        if ((s[0] | s[1] | s[2] | s[3]) == 0)
            s[0] = 1; // The all-zero state is invalid.
    }

    /// Returns the next 64-bit random value.
    uint64_t next()
    {
        const uint64_t result = rotl64(s[1] * 5, 7) * 9;
        const uint64_t t = s[1] << 17;

        s[2] ^= s[0];
        s[3] ^= s[1];
        s[1] ^= s[2];
        s[0] ^= s[3];
        s[2] ^= t;
        s[3] = rotl64(s[3], 45);
        return result;
    }

    /// Returns a uniform double in [0, 1) with 53-bit resolution.
    ///
    /// The bit manipulation keeps results identical across compilers
    /// and platforms, unlike std::uniform_real_distribution.
    double next_double()
    {
        return (next() >> 11) * 0x1.0p-53;
    }
};

/// Accessor for the thread-local generator shared by all boxes.
///
/// Seeded once per thread from std::random_device via splitmix64.
/// Successive calls continue the same sequence, which replicates the
/// behavior of the former per-box cached VSL streams without making
/// Box objects mutable.
inline Xoshiro256ss &thread_local_rng()
{
    thread_local Xoshiro256ss rng = [] {
        std::random_device rd;
        const uint64_t seed_value = (uint64_t(rd()) << 32) | rd();
        Xoshiro256ss instance{};
        instance.seed(seed_value);
        return instance;
    }();
    return rng;
}

#endif
