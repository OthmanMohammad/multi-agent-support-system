"use client";

import type { JSX } from "react";
import { useState } from "react";
import { useSession } from "next-auth/react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Camera, Loader2, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "@/lib/utils/toast";
import { cn } from "@/lib/utils";

const profileSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(50),
  email: z.string().email("Invalid email address"),
  bio: z.string().max(200, "Bio must be less than 200 characters").optional(),
  company: z.string().max(100).optional(),
  location: z.string().max(100).optional(),
  website: z.string().url("Invalid URL").optional().or(z.literal("")),
});

type ProfileFormData = z.infer<typeof profileSchema>;

/**
 * Profile Settings Component
 * Manage user profile information
 */
// eslint-disable-next-line complexity -- Complex form component with multiple fields and validation
export function ProfileSettings(): JSX.Element {
  const { data: session } = useSession();
  const [isUploading, setIsUploading] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState(session?.user?.image || "");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: session?.user?.name || "",
      email: session?.user?.email || "",
      bio: "",
      company: "",
      location: "",
      website: "",
    },
  });

  const onSubmit = async (_data: ProfileFormData): Promise<void> => {
    try {
      // TODO: Implement profile update API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      toast.success("Profile updated", {
        description: "Your profile has been updated successfully.",
      });
    } catch (_error) {
      toast.error("Failed to update profile", {
        description:
          _error instanceof Error ? _error.message : "Please try again.",
      });
    }
  };

  const handleAvatarChange = async (
    e: React.ChangeEvent<HTMLInputElement>
  ): Promise<void> => {
    const file = e.target.files?.[0];
    if (!file) {
      return;
    }

    // Validate file type
    if (!file.type.startsWith("image/")) {
      toast.error("Invalid file type", {
        description: "Please upload an image file.",
      });
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error("File too large", {
        description: "Maximum file size is 2MB.",
      });
      return;
    }

    setIsUploading(true);

    try {
      // TODO: Implement avatar upload
      // For now, create local preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setAvatarUrl(e.target?.result as string);
      };
      reader.readAsDataURL(file);

      await new Promise((resolve) => setTimeout(resolve, 1000));

      toast.success("Avatar uploaded", {
        description: "Your profile picture has been updated.",
      });
    } catch (_error) {
      toast.error("Failed to upload avatar", {
        description: "Please try again.",
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Profile Settings</h2>
        <p className="mt-1 text-sm text-foreground-secondary">
          Update your personal information and profile picture
        </p>
      </div>

      {/* Avatar Upload */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <h3 className="mb-4 font-semibold">Profile Picture</h3>
        <div className="flex items-center gap-6">
          <div className="relative">
            <div className="h-24 w-24 overflow-hidden rounded-full bg-surface-hover">
              {avatarUrl ? (
                /* eslint-disable-next-line @next/next/no-img-element -- Dynamic user avatar URL */
                <img
                  src={avatarUrl}
                  alt="Profile"
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-2xl font-bold text-foreground-secondary">
                  {session?.user?.name?.[0]?.toUpperCase() || "?"}
                </div>
              )}
            </div>
            <label
              htmlFor="avatar-upload"
              className={cn(
                "absolute bottom-0 right-0 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-accent text-accent-foreground shadow-lg transition-opacity hover:opacity-80",
                isUploading && "pointer-events-none opacity-50"
              )}
            >
              {isUploading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Camera className="h-4 w-4" />
              )}
            </label>
            <input
              id="avatar-upload"
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleAvatarChange}
              disabled={isUploading}
            />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium">Upload a new profile picture</p>
            <p className="mt-1 text-xs text-foreground-secondary">
              JPG, PNG or GIF. Max size 2MB.
            </p>
          </div>
        </div>
      </div>

      {/* Profile Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="rounded-lg border border-border bg-surface p-6">
          <h3 className="mb-4 font-semibold">Personal Information</h3>
          <div className="space-y-4">
            {/* Name */}
            <div>
              <Label htmlFor="name">Full Name *</Label>
              <Input
                id="name"
                {...register("name")}
                className={cn(errors.name && "border-destructive")}
              />
              {errors.name && (
                <p className="mt-1 text-xs text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>

            {/* Email */}
            <div>
              <Label htmlFor="email">Email Address *</Label>
              <Input
                id="email"
                type="email"
                {...register("email")}
                className={cn(errors.email && "border-destructive")}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-destructive">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Bio */}
            <div>
              <Label htmlFor="bio">Bio</Label>
              <textarea
                id="bio"
                {...register("bio")}
                rows={3}
                className={cn(
                  "w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none placeholder:text-foreground-secondary focus:border-accent focus:ring-2 focus:ring-accent/20",
                  errors.bio && "border-destructive"
                )}
                placeholder="Tell us about yourself..."
              />
              {errors.bio && (
                <p className="mt-1 text-xs text-destructive">
                  {errors.bio.message}
                </p>
              )}
            </div>

            {/* Company */}
            <div>
              <Label htmlFor="company">Company</Label>
              <Input
                id="company"
                {...register("company")}
                placeholder="Acme Inc."
              />
            </div>

            {/* Location */}
            <div>
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                {...register("location")}
                placeholder="San Francisco, CA"
              />
            </div>

            {/* Website */}
            <div>
              <Label htmlFor="website">Website</Label>
              <Input
                id="website"
                type="url"
                {...register("website")}
                placeholder="https://example.com"
                className={cn(errors.website && "border-destructive")}
              />
              {errors.website && (
                <p className="mt-1 text-xs text-destructive">
                  {errors.website.message}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-between rounded-lg border border-border bg-surface p-4">
          <p className="text-sm text-foreground-secondary">
            {isDirty ? "You have unsaved changes" : "All changes saved"}
          </p>
          <Button type="submit" disabled={!isDirty || isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </form>

      {/* Danger Zone */}
      <div className="rounded-lg border border-destructive bg-destructive/5 p-6">
        <h3 className="mb-2 font-semibold text-destructive">Danger Zone</h3>
        <p className="mb-4 text-sm text-foreground-secondary">
          Irreversible and destructive actions
        </p>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Delete Account</p>
            <p className="text-xs text-foreground-secondary">
              Permanently delete your account and all data
            </p>
          </div>
          <Button variant="destructive" size="sm">
            Delete Account
          </Button>
        </div>
      </div>
    </div>
  );
}
