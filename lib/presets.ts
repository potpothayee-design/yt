import type { AspectId, StyleId } from './styles'

export interface PromptPreset {
  id: string
  title: string
  emoji: string
  tag: string
  style: StyleId
  aspect: AspectId
  prompt: string
  motion: string
}

/** The 7 viral presets, ready to fire. */
export const PRESETS: PromptPreset[] = [
  {
    id: 'cardboard-ferrari',
    title: 'Tiny Workers Building Cardboard Ferrari',
    emoji: '🏎️',
    tag: 'Build',
    style: 'photoreal',
    aspect: '9:16',
    prompt:
      'A team of tiny 5cm tall construction workers in orange hi-vis vests and yellow hard hats swarming over a life-size ' +
      'Ferrari sports car built entirely from brown corrugated cardboard puzzle pieces. Some workers ride miniature cranes ' +
      'lifting a giant cardboard door panel into place, others weld glowing seams with tiny sparks, one foreman stands on ' +
      'the hood pointing at a blueprint. Scattered laser-cut cardboard sheets and puzzle offcuts on the workshop floor, ' +
      'warm afternoon sunbeams through a garage window, floating dust motes.',
    motion:
      'Slow cinematic dolly-in toward the car door as tiny workers hammer and the crane lowers a cardboard panel into the slot, ' +
      'sparks drifting, dust floating in the sunbeam, subtle handheld camera sway.',
  },
  {
    id: 'hotwheels-disassembly',
    title: 'Tiny Workers Disassembling Hot Wheels',
    emoji: '🔩',
    tag: 'Teardown',
    style: 'photoreal',
    aspect: '9:16',
    prompt:
      'Macro shot of dozens of tiny 4cm workers in blue mechanic overalls completely disassembling a die-cast Hot Wheels toy ' +
      'car on a workshop table. Teams unbolt the metal body shell with oversized power tools, a mini forklift carries away a ' +
      'single red wheel, the chassis is hoisted on a miniature scissor lift, tiny screws and springs laid out in neat rows ' +
      'on a grid mat. Cinematic overhead key light, glossy paint reflections, extreme detail on chipped die-cast paint.',
    motion:
      'Smooth orbit around the half-stripped Hot Wheels car while workers unscrew panels, the wheel rolls across the table, ' +
      'tools spin, tiny sparks fly, shallow depth of field breathing.',
  },
  {
    id: 'pixar-sad-car',
    title: 'Pixar Sad Cardboard Car',
    emoji: '🥺',
    tag: 'Emotional',
    style: 'pixar',
    aspect: '9:16',
    prompt:
      'An adorable little cardboard car character with huge glossy expressive eyes for headlights, sitting alone in the rain ' +
      'in an empty parking lot at dusk. Its corrugated cardboard body is soggy and drooping at the corners, one bumper flap ' +
      'hanging loose, a single raindrop rolling down like a tear. Puddles reflect a warm distant streetlight. ' +
      'Heartbreaking Pixar short film emotional close up, cinematic depth, moody teal and amber color grade.',
    motion:
      'Slow push-in on the sad cardboard car as rain falls, its eyes blink once and look down, a tear-like droplet rolls off ' +
      'the bumper into the puddle creating ripples, streetlight flickers gently.',
  },
  {
    id: 'toy-story-alive',
    title: 'Toy Story Cardboard Comes Alive',
    emoji: '✨',
    tag: 'Magic',
    style: 'pixar',
    aspect: '9:16',
    prompt:
      "The moment a flat stack of brown cardboard puzzle pieces on a child's bedroom floor magically springs to life and " +
      'self-assembles into a cheerful cardboard robot toy with big friendly eyes. Pieces float and snap together mid-air ' +
      'trailing golden sparkle dust, the robot stretches its arms and grins for the first time. Moonlight through the window, ' +
      'toy box and crayons in the background, Toy Story style wonder and warmth, magical rim lighting.',
    motion:
      'Cardboard pieces lift off the floor and snap together mid-air in sequence with golden sparkles, the finished robot ' +
      'stretches, blinks, waves at camera, gentle crane-up camera move.',
  },
  {
    id: 'asmr-engine',
    title: 'ASMR Cardboard Engine',
    emoji: '🔊',
    tag: 'ASMR',
    style: 'kraft',
    aspect: '9:16',
    prompt:
      'Extreme macro ASMR shot of a fully working V8 engine crafted entirely from brown kraft cardboard puzzle pieces, ' +
      'pistons and camshafts made of rolled corrugated paper, cardboard belts and paper hoses, each part slotting together ' +
      'with satisfying precision. Clean seamless beige paper backdrop, soft diffused studio softbox lighting, ' +
      'razor sharp texture detail on every corrugated flute, oddly satisfying product photography.',
    motion:
      'Ultra slow macro push along the cardboard engine as pistons pump up and down, the paper fan belt rotates, ' +
      'one puzzle piece slots in perfectly, tiny paper fibers catching the light.',
  },
  {
    id: 'dual-restoration',
    title: 'Dual Restoration Split Screen',
    emoji: '🪄',
    tag: 'Split Screen',
    style: 'photoreal',
    aspect: '9:16',
    prompt:
      'Perfect vertical split screen composition. LEFT HALF: a rusted, dented, filthy abandoned classic car body covered in ' +
      'grime under cold blue light. RIGHT HALF: the exact same car fully restored, mirror-polished glossy red paint, chrome ' +
      'gleaming under warm golden light. Tiny 5cm workers in overalls crawl across both halves, sanding and scrubbing on the ' +
      'left, waxing and buffing on the right. Crisp centre dividing line, dramatic before-and-after satisfaction, ultra detailed.',
    motion:
      'The centre split line sweeps slowly left to right transforming rust into polished chrome as tiny workers buff the ' +
      'surface, light shifts from cold blue to warm gold, reflections bloom.',
  },
  {
    id: '3am-tiny-city',
    title: '3AM Tiny City',
    emoji: '🌃',
    tag: 'Night',
    style: 'photoreal',
    aspect: '9:16',
    prompt:
      'A sprawling miniature city built from cardboard boxes and puzzle pieces at 3AM, seen from a low street-level macro ' +
      'angle. Tiny night-shift workers in reflective vests repair a glowing cardboard streetlight from a mini cherry picker, ' +
      'a miniature street sweeper crawls past, warm window lights glow from inside the cardboard skyscrapers, wet asphalt ' +
      'reflects neon signage, thin fog rolling between the buildings. Blade Runner meets diorama, cinematic teal and orange.',
    motion:
      'Slow low dolly down the miniature street as fog drifts, streetlight flickers on, the cherry picker rises, ' +
      'tiny neon signs buzz and reflect in the wet cardboard asphalt.',
  },
]
