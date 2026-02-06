import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { AlertCircle, Home } from 'lucide-react';
import Link from 'next/link';

interface RoomErrorProps {
  title: string;
  message: string;
  action?: React.ReactNode;
}

export function RoomError({ title, message, action }: RoomErrorProps) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-muted/30">
      <Card className="w-full max-w-md shadow-lg border-destructive/20">
        <CardHeader className="text-center">
          <div className="mx-auto bg-destructive/10 p-3 rounded-full w-fit mb-2">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <CardTitle className="text-xl text-destructive">{title}</CardTitle>
          <CardDescription className="text-base mt-2">
            {message}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center">
          {action}
        </CardContent>
        <CardFooter className="justify-center border-t pt-4">
          <Link href="/">
            <Button variant="ghost" className="gap-2">
              <Home className="h-4 w-4" /> Go to Home
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}
