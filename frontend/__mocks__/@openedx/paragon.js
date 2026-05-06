/**
 * Minimal Paragon stub for Jest.
 *
 * Paragon ships as ESM only, which Jest can't load without a full Babel
 * transform pipeline. These stubs render plain HTML elements so tests focus on
 * component behaviour (does setFormField get called? are fields accessible?)
 * rather than Paragon internals.
 */

const React = require('react');

const Form = ({ children }) => React.createElement('form', null, children);

Form.Group = ({ children, controlId }) =>
  React.createElement('div', { 'data-testid': controlId }, children);

Form.Control = ({ as, floatingLabel, name, type, value, onChange, children, placeholder }) => {
  const label = React.createElement('label', { htmlFor: name }, floatingLabel);
  if (as === 'select') {
    const select = React.createElement(
      'select',
      { id: name, name, value: value || '', onChange, 'aria-label': floatingLabel },
      children,
    );
    return React.createElement(React.Fragment, null, label, select);
  }
  const input = React.createElement('input', {
    id: name,
    name,
    type: type || 'text',
    value: value || '',
    onChange,
    placeholder,
    'aria-label': floatingLabel,
  });
  return React.createElement(React.Fragment, null, label, input);
};

Form.Text = ({ children }) => React.createElement('small', null, children);

module.exports = { Form };
