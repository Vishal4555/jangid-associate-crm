import { z } from "zod";

export const caseSchema = z.object({
  case_no: z.string().min(1, "Case No is required"),

  receive_date: z.string().optional(),

  bank: z.string().optional(),

  branch: z.string().optional(),

  applicant: z.string().min(1, "Applicant name is required"),

  product_type: z.string().optional(),

  loan_type: z.string().optional(),

  address: z.string().optional(),

  city: z.string().optional(),

  mobile: z
    .string()
    .min(10, "Mobile must be at least 10 digits")
    .max(10, "Mobile must be 10 digits")
    .optional()
    .or(z.literal("")),

  executive: z.string().optional(),

  status: z.enum([
    "Pending",
    "Positive",
    "Negative",
  ]),

  negative_reason: z.string().optional(),

  landmark: z.string().optional(),

  remarks: z.string().optional(),

  next_follow_up_at: z.string().optional(),

  follow_up_note: z.string().optional(),
});

export type CaseFormData = z.infer<typeof caseSchema>;
