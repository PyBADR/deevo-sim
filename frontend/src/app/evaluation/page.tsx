/**
 * /evaluation — FROZEN
 *
 * This public archive page is demoted.
 * All evaluation and monitoring intelligence lives inside /command-center.
 * This route redirects to the command surface.
 */

import { redirect } from 'next/navigation';

export default function EvaluationRedirect() {
  redirect('/command-center');
}
