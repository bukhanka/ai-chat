import { TraditionalForm } from "@/components/traditional-form"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function TraditionalFormPage() {
  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Traditional Form-Based Approach</h1>
        <Link href="/" passHref>
          <Button variant="outline">Back to Home</Button>
        </Link>
      </div>
      <TraditionalForm />
    </div>
  )
}

