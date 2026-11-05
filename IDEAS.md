# Ideas

Things the owner liked and wants done later. Ask for one by its name; each says what it is and
what to watch for. Remove an idea from here once it is built.

## The roof and sky views

Agreed on 2026-11-02, after the flight and the roofs were made smooth and solid. All of these are
for the views from up high only (`v.eye >= 10`) - the street stays exactly as it is - and each
has to keep the roof and the plane under 33 ms a frame at 300x90, checked like every speed change
here. Suggested order: 1 first, then as wanted. (Distant skyline shapes are built.)

1. **Proper rooftops.** The renderer only knows building fronts, so a roof seen from above is
   faked by stacking thin slices of front: up close it reads as stripes. Draw real roofs - the
   flat top in a roof texture, with air-conditioning units, water tanks and now and then a
   stairwell hut - so near buildings look solid from above.
2. **Red aircraft warning lights** blinking on the tallest towers, the way a real skyline looks at
   night. From the plane they mark out downtown. Cheap: a few points.
4. **Moving lights on the roads.** Streams of white headlights one way and red tail lights the
   other along the avenues and the highway, much further out than cars are drawn now: from up
   high, traffic is the most alive part of a city at night.
5. **A glow over the city at the horizon.** A faint orange haze where the city lights the sky
   from below, just above the horizon; the moon and the far lights still show through it.
6. **Clouds under the plane.** A few wisps passing under it while it cruises, the city lights
   showing through the gaps. For the flight only.
