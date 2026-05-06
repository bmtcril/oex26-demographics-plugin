import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DemographicsFields from './DemographicsFields';

const baseProps = {
  formFields: {},
  setFormField: jest.fn(),
};

describe('DemographicsFields', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders the pronouns text input', () => {
    render(<DemographicsFields {...baseProps} />);
    expect(screen.getByRole('textbox', { name: /pronouns/i })).toBeInTheDocument();
  });

  it('renders the department select', () => {
    render(<DemographicsFields {...baseProps} />);
    expect(screen.getByRole('combobox', { name: /department/i })).toBeInTheDocument();
  });

  it('reflects formFields values', () => {
    render(
      <DemographicsFields
        {...baseProps}
        formFields={{ pronouns: 'they/them', department: 'eng' }}
      />,
    );
    expect(screen.getByRole('textbox', { name: /pronouns/i })).toHaveValue('they/them');
    expect(screen.getByRole('combobox', { name: /department/i })).toHaveValue('eng');
  });

  it('calls setFormField when pronouns changes', async () => {
    const setFormField = jest.fn();
    render(<DemographicsFields formFields={{}} setFormField={setFormField} />);
    await userEvent.type(screen.getByRole('textbox', { name: /pronouns/i }), 'she/her');
    expect(setFormField).toHaveBeenCalled();
  });

  it('calls setFormField when department changes', async () => {
    const setFormField = jest.fn();
    render(<DemographicsFields formFields={{}} setFormField={setFormField} />);
    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: /department/i }),
      'ops',
    );
    expect(setFormField).toHaveBeenCalled();
  });

  it('renders custom departments when provided', () => {
    const departments = [{ value: 'custom', label: 'Custom Dept' }];
    render(<DemographicsFields {...baseProps} departments={departments} />);
    expect(screen.getByRole('option', { name: 'Custom Dept' })).toBeInTheDocument();
  });

  it('does not render default departments when custom ones are provided', () => {
    const departments = [{ value: 'custom', label: 'Custom Dept' }];
    render(<DemographicsFields {...baseProps} departments={departments} />);
    expect(screen.queryByRole('option', { name: 'Engineering' })).not.toBeInTheDocument();
  });
});
