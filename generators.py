import math
from collections.abc import Callable
import typing

type Color = typing.List[float] # R, G, B   0.0 - 1.0
type Generator = Callable[[float, int, int], Color] # time in seconds, light N, total lights


# Positive sin(x), values ranging from 0.0 to 1.0
def sinp(x):
    return (math.sin(x) + 1.0) * 0.5


# If x at a is 0 and x at b is 1, then this is proper lerp
def lerp(a, b, x: float):
    return a * (1-x) +  b * x


# TODO: Replace bad implementation
def noise(x):
    return (sinp(2 * x) + sinp(math.pi * x)) * 0.5


# Nice pastel rainbow gradient, from x=0.0 to x=1.0
def rainbow_gradient(x) -> Color:
    return [sinp(2.0 * math.pi * x),
            sinp(2.0 * math.pi * (x + 1.0 / 3.0)),
            sinp(2.0 * math.pi * (x + 2.0 / 3.0))]


# def palette(bias: tuple[float, float, float],
#             scale: tuple[float, float, float],
#             interval: tuple[float, float, float],
#             phase: tuple[float, float, float]
#             ) -> Generator:
#     def helper(time: float, _1: int, _2: int) -> Color:
#         color = [0, 0, 0]
#         for channel in range(3):
#             color[channel] = bias[channel] + scale[channel] * math.cos( math.pi * 2 * ( interval[channel] * time + phase[channel]) )
#         return color
#     return helper


# Constructs a generator emitting given color
def solid_color(color: Color) -> Generator:
    def helper(*_):
        return color
    return helper


# Define colors as generators
red: Generator = solid_color([1.0, 0.0, 0.0])
green: Generator = solid_color([0.0, 1.0, 0.0])
blue: Generator = solid_color([0.0, 0.0, 1.0])
black: Generator = solid_color([0.0, 0.0, 0.0])
white: Generator = solid_color([1.0, 1.0, 1.0])


# Generates white colored noise by time
def noise_generator(time, *_) -> Color:
    x = noise(time  * 0.1)
    return [x, x, x]
    

# Converts two generators into one, splitting them at light `split_at`. 
def split(split_at: int, generator1: Generator, generator2: Generator) -> Generator:
    def helper(time, light, total_lights):
        if light < split_at:
            return generator1(time, light, total_lights)
        else:
            return generator2(time, light, total_lights)
    return helper


# Shifts generators lights towards the end by `by` lights, while
# putting overflowing lights to the beginning.
def rotate(by: int, generator: Generator) -> Generator:
    def helper(time, light, total_lights):
        return generator(time, (light - by) % total_lights, total_lights)
    return helper


# Flips a given generator, so that the first light becomes the last and so on.
def mirror(generator: Generator) -> Generator:
    def helper(time, light, total_lights):
        return generator(time, total_lights - 1 - light, total_lights)
    return helper


# Shifts all lights of generator in time by shift
def time_shift(shift: float, generator: Generator) -> Generator:
    def helper(time, light, total_lights):
        return generator(time + shift, light, total_lights)
    return helper


# Shifts generators time of lamps, so that the first lamp is shifted by
# start_time_shift, and last by end_time_shift, while the lights in between
# make a transition from first lamp to last.
def time_shift_gradient(start_time_shift: float, end_time_shift: float, generator: Generator) -> Generator:
    def helper(time, light, total_lights):
        light_pos = light / total_lights
        time_shift = (end_time_shift - start_time_shift) * light_pos + start_time_shift
        return generator(time + time_shift, light, total_lights)
    return helper


# Scales generators timescale
def time_scale(factor: float, generator: Generator) -> Generator:
    def helper(time, light, total_lights):
        return generator(time * factor, light, total_lights)
    return helper


# Turns all generators lights on and off smoothly by time
def shimmer(speed: float, generator: Generator) -> Generator:
    def helper(time, light, total_lights):
        phase = 2 * math.pi * time * speed
        color = list(generator(time, light, total_lights))
        for channel in range(3):
            color[channel] *= sinp(phase)
        return color
    return helper


# Multiplies given generators together by their color channels
def product(*generators) -> Generator:
    def helper(time, light, total_lights):
        colors = [g(time, light, total_lights) for g in generators]
        return [math.prod(a) for a in zip(*colors)]
    return helper


# Sums given generators together by their color channels 
def add(*generators) -> Generator:
    def helper(time, light, total_lights):
        colors = [g(time, light, total_lights) for g in generators]
        return [sum(a) for a in zip(*colors)]
    return helper


# Transitions from generator1 to generator2 by x, from 0.0 to 1.0
def mix(x: float, generator1: Generator, generator2: Generator) -> Generator:
    def helper(time, light, total_lights):
        color1 = generator1(time, light, total_lights)
        color2 = generator2(time, light, total_lights)
        return [lerp(a[0], a[1], x) for a in zip(color1, color2)]
    return helper


# Makes lights symmetrical by their centermost light
def mirror_split(generator: Generator) -> Generator:
    def helper(time, light, total_lights):
        return split(int(total_lights / 2), generator, mirror(generator))(time, light, total_lights)
    return helper


# Separates colors in time
def abberration(strength: float, generator: Generator):
    def helper(time, light, total_lights):
        return [generator(time + strength * (x/3), light, total_lights)[x] for x in range(3)]
    return helper


# Makes the lights go trough rainbow colors by time
def rainbow(time, *_) -> Color:
    return rainbow_gradient(time)


ytp: Generator = \
    mirror_split(
        product(
            time_scale(
                1.0,
                time_shift_gradient(
                    0.0,
                    40.0,
                    noise_generator
                )
            ),
            time_scale(
                1.0 / 5.0,
                time_shift_gradient(
                    0.0,
                    2.0,
                    add(
                        shimmer(
                            1.0,
                            solid_color([8/255, 240/255, 250/255])
                        ),
                        time_shift(
                            0.5,
                            shimmer(
                                1.0,
                                solid_color([181/255, 129/255, 255/255]),
                            )
                        )
                    ),
                )
            )
        )
    )


color_noise: Generator = \
    time_scale(
        5.0,
        time_shift_gradient(
            0.0,
            80.0,
            add(
                product(
                    red,
                    noise_generator
                ),
                product(
                    green,
                    time_shift(
                        100,
                        time_scale(
                            0.4,
                            noise_generator
                        )
                    )
                ),
                product(
                    blue,
                    time_shift(
                        200,
                        time_scale(
                            0.7,
                            noise_generator
                        )
                    )
                )
            )
        )
    )
    

metallic_noise: Generator = \
    time_scale(
        3,
        time_shift_gradient(
            0, 80,
            abberration(
                10,
                noise_generator
            )
        )
    )


# def demo(time: float, light: int, total_lights: int) -> Color:
#     l_pos = light / total_lights
#     biases = (1.0, 0.2, 0.2)
#     scales = (0.0, 0.2, 0.2)
#     intervals = (0.0, 0.25, 0.3)
#     phases = (l_pos, l_pos, l_pos)
#     foo_palette = palette(biases, scales, intervals, phases)
#     return (
#         time_shift_gradient( # Shift shimmer effect in time between lights
#             shimmer(
#                 time_shift_gradient( # Undo time shift for palette
#                     foo_palette,
#                     -1.0,
#                     0.0
#                 ),
#                 1.0 / 14.0
#             ),
#             0.0,
#             1.0
#         )(time, light, total_lights)
#     )

