/**
 * /decision — FROZEN
 *
 * This public archive page is demoted.
 * All decision intelligence lives inside /command-center.
 * This route redirects to the command surface.
 */

import { redirect } from 'next/navigation';

export default function DecisionRedirect() {
  redirect('/command-center');
}
