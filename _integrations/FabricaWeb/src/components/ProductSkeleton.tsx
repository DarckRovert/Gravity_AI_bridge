export default function ProductSkeleton() {
    return (
        <div className="bg-white rounded-3xl overflow-hidden shadow-md animate-pulse p-4 flex flex-col gap-4">
            <div className="aspect-square bg-gray-200 rounded-2xl w-full" />
            <div className="space-y-3">
                <div className="h-6 bg-gray-200 rounded-full w-3/4" />
                <div className="h-4 bg-gray-200 rounded-full w-1/2" />
                <div className="h-4 bg-gray-200 rounded-full w-full" />
                <div className="h-4 bg-gray-200 rounded-full w-2/3" />
            </div>
            <div className="mt-auto flex justify-between items-center bg-gray-50 -mx-4 -mb-4 p-4">
                <div className="h-6 bg-gray-200 rounded-full w-20" />
                <div className="h-10 bg-gray-200 rounded-xl w-24" />
            </div>
        </div>
    );
}
