// JS mirror of the motion tokens in tokens.css, so Motion and GSAP animate with the same vocabulary.
export const ease = {
  out: [0.16, 1, 0.3, 1] as const,
  inout: [0.76, 0, 0.24, 1] as const,
  gsapOut: "expo.out",
  gsapInout: "power4.inOut",
};

export const dur = {
  instant: 0.12,
  quick: 0.22,
  base: 0.42,
  slow: 0.7,
  intro: 1.4,
  ambient: 24,
};

export const stagger = { grid: 0.028, list: 0.06 };

export const spring = { type: "spring", stiffness: 380, damping: 32 } as const;
export const softSpring = { type: "spring", stiffness: 150, damping: 18, mass: 0.6 } as const;
