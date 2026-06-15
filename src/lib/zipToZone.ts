/**
 * Maps a US zip code to a Japan Post destination zone (1–5).
 * Zone 1 = closest to Japan (Hawaii/Guam), Zone 5 = East Coast.
 * Used to look up shipping rates from the DB.
 */
export function zipToZone(zip: string): number {
  const p = parseInt(zip.slice(0, 3), 10)
  if (isNaN(p)) return 3

  // Zone 1: Hawaii (967–968), Guam (969)
  if (p >= 967 && p <= 969) return 1

  // Zone 2: California, Oregon, Washington, Alaska, Nevada, Arizona
  if (p >= 900 && p <= 961) return 2
  if (p >= 970 && p <= 979) return 2
  if (p >= 980 && p <= 999) return 2
  if (p >= 889 && p <= 898) return 2
  if (p >= 850 && p <= 865) return 2

  // Zone 3: Mountain states (CO, WY, ID, UT, NM, MT)
  if (p >= 800 && p <= 816) return 3
  if (p >= 820 && p <= 847) return 3
  if (p >= 870 && p <= 884) return 3
  if (p >= 590 && p <= 599) return 3

  // Zone 4: Central / Midwest / South
  if (p >= 460 && p <= 528) return 4  // IN, MI, IA
  if (p >= 530 && p <= 588) return 4  // WI, MN, SD, ND
  if (p >= 600 && p <= 693) return 4  // IL, MO, KS, NE
  if (p >= 700 && p <= 799) return 4  // LA, AR, OK, TX

  // Zone 5: East Coast + Southeast
  if (p >= 10  && p <= 89)  return 5  // New England + NJ (010–089)
  if (p >= 100 && p <= 459) return 5  // NY through KY/OH

  return 3 // default for any unmatched prefix
}
