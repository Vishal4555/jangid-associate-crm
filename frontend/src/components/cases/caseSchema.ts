import { z } from "zod";

export const caseSchema = z.object({
  visit_type: z.enum(["Residence", "Office", "Permanent", "Business", "Other"]),
  los_no: z.string().trim().min(1, "LOS / Application No is required").max(100, "LOS No must be 100 characters or fewer"),

  receive_date: z.string().optional(),

  bank: z.string().optional(),
  company_id: z.number().int().positive().optional(),
  company: z.string().optional(),
  district_id: z.number().int().positive().optional(),
  district: z.string().optional(),

  applicant: z.string().min(1, "Applicant name is required"),

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

});

export type CaseFormData = z.infer<typeof caseSchema>;
