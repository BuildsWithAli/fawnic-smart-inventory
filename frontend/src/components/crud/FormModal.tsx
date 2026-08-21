import { useEffect, useState } from "react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import type { FieldDef } from "../../types/crud";

interface FormModalProps<T extends { id: number }> {
  isOpen: boolean;
  title: string;
  fields: FieldDef<T>[];
  initialValues: Record<string, unknown>;
  isSaving?: boolean;
  errors?: Record<string, string>;
  onClose: () => void;
  onSubmit: (values: Record<string, unknown>) => void;
}

export function FormModal<T extends { id: number }>({
  isOpen,
  title,
  fields,
  initialValues,
  isSaving,
  errors = {},
  onClose,
  onSubmit,
}: FormModalProps<T>) {
  const [values, setValues] = useState<Record<string, unknown>>(initialValues);

  useEffect(() => {
    if (isOpen) setValues(initialValues);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const handleChange = (name: string, value: string) => {
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={() => onSubmit(values)} isLoading={isSaving}>
            Save
          </Button>
        </>
      }
    >
      <form
        className="grid grid-cols-1 gap-4 sm:grid-cols-2"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit(values);
        }}
      >
        {fields.map((field) => {
          const value = (values[field.name] as string | number | undefined) ?? "";
          if (field.type === "select") {
            return (
              <Select
                key={field.name}
                label={field.label}
                required={field.required}
                value={String(value)}
                error={errors[field.name]}
                onChange={(e) => handleChange(field.name, e.target.value)}
                className="sm:col-span-1"
              >
                <option value="" disabled>
                  Select {field.label.toLowerCase()}
                </option>
                {field.options?.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Select>
            );
          }
          if (field.type === "textarea") {
            return (
              <label key={field.name} className="flex flex-col gap-1.5 sm:col-span-2">
                <span className="text-sm font-medium text-ink-soft">{field.label}</span>
                <textarea
                  value={String(value)}
                  required={field.required}
                  placeholder={field.placeholder}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                />
                {errors[field.name] && <span className="text-xs text-danger">{errors[field.name]}</span>}
              </label>
            );
          }
          return (
            <Input
              key={field.name}
              label={field.label}
              type={field.type}
              required={field.required}
              placeholder={field.placeholder}
              step={field.step}
              min={field.min}
              value={String(value)}
              error={errors[field.name]}
              onChange={(e) => handleChange(field.name, e.target.value)}
            />
          );
        })}
      </form>
    </Modal>
  );
}
