/**
 * DemographicsFields
 *
 * Plugin component for the registration additional-fields slot:
 *   org.openedx.frontend.authn.register.additional_fields.v1
 *
 * Renders two optional form fields — pronouns (free text) and department
 * (select) — and wires them into the parent registration form via the
 * slot-provided setFormField handler.
 *
 * The workshop uses this component as the live-coding target for
 * "what a plugin that fills a slot looks like."
 */

import React from "react";
import { Form } from "@openedx/paragon";

/**
 * Default department list.  Operators override this via the Tutor plugin by
 * setting DEMOGRAPHICS_DEPARTMENTS in the MFE environment config, which is
 * passed down as the `departments` prop when registering the slot.
 */
const DEFAULT_DEPARTMENTS = [
  { value: "eng", label: "Engineering" },
  { value: "ops", label: "Operations" },
  { value: "edu", label: "Education" },
  { value: "mkt", label: "Marketing" },
  { value: "fin", label: "Finance" },
];

/**
 * @param {object}   props
 * @param {Record<string,string>} props.formFields   - Current registration form values.
 * @param {Function} props.setFormField              - Form change handler; called with a
 *     synthetic event whose target has `name` and `value`.
 * @param {Array<{value:string, label:string}>} [props.departments] - Override the
 *     default department list.  Pass via slot pluginProps in env.config.jsx.
 */
const DemographicsFields = ({
  formFields,
  setFormField,
  departments = DEFAULT_DEPARTMENTS,
}) => (
  <>
    <Form.Group controlId="demographics-pronouns">
      <Form.Control
        name="pronouns"
        type="text"
        floatingLabel="Pronouns (optional)"
        placeholder="e.g. she/her, they/them"
        value={formFields.pronouns || ""}
        onChange={setFormField}
      />
      <Form.Text>How should we address you?</Form.Text>
    </Form.Group>

    <Form.Group controlId="demographics-department">
      <Form.Control
        as="select"
        name="department"
        floatingLabel="Department (optional)"
        value={formFields.department || ""}
        onChange={setFormField}
      >
        <option value="">— Select a department —</option>
        {departments.map(({ value, label }) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </Form.Control>
    </Form.Group>
  </>
);

export default DemographicsFields;
